# Python program to connect
# to mysql database
 
 
# dbConn.py
"""
Robust drop-in replacement for the original dbConn class.

Public API preserved:
  - connect(user, password, host, database, auth='mysql_native_password', port=3306, autocommit=True, retries=10, delay=3)
  - execute(query, args=None)
  - close()

Behavior:
  - Auto-pings and reconnects when connection is stale.
  - Retries queries on OperationalError with exponential backoff.
  - Ensures cursors are closed on all code paths.
  - Thread-safe via an RLock.
  - Returns same types as original: SELECT -> list of tuples; non-SELECT -> affected rowcount.
"""

from typing import Optional, Any, Tuple
import mysql.connector
from mysql.connector import Error, OperationalError
import time
import threading
import traceback

class dbConn():
    def __init__(self):
        self.connection: Optional[mysql.connector.connection_cext.CMySQLConnection] = None
        self.cursor = None
        self._lock = threading.RLock()
        self._connect_params = None
        # Controls for execute retries
        self.default_query_retries = 3
        self.default_query_backoff = 0.5

    def connect(self, user, password, host, database, auth = 'mysql_native_password',
                port = 3306, autocommit=True, retries=10, delay=3):
        """
        Establish connection and store params for later reconnects.
        This method keeps the same signature as the original.
        """
        self._connect_params = {
            'user': user,
            'password': password,
            'host': host,
            'database': database,
            'auth_plugin': auth,
            'port': port,
            'autocommit': autocommit
        }

        attempt = 0
        while attempt < retries:
            attempt += 1
            try:
                with self._lock:
                    self.connection = mysql.connector.connect(**self._connect_params)
                    try:
                        # ensure autocommit attribute if available
                        self.connection.autocommit = autocommit
                    except Exception:
                        pass
                print(f"Connected to DB on attempt {attempt}")
                return
            except Error as e:
                print(f"DB connection failed ({e}), retrying in {delay}s... (attempt {attempt}/{retries})")
                time.sleep(delay)

        raise RuntimeError("Could not connect to DB after retries")

    def _recreate_connection(self, retries=5, base_delay=1.0):
        """
        Recreate connection using stored params with exponential backoff.
        """
        if not self._connect_params:
            raise RuntimeError("No connection parameters available to reconnect")

        attempt = 0
        while attempt < retries:
            attempt += 1
            try:
                with self._lock:
                    # close existing if present
                    try:
                        if self.connection:
                            self.connection.close()
                    except Exception:
                        pass
                    self.connection = mysql.connector.connect(**self._connect_params)
                    try:
                        self.connection.autocommit = self._connect_params.get('autocommit', True)
                    except Exception:
                        pass
                print(f"Reconnected to DB on attempt {attempt}")
                return
            except Error as e:
                delay = base_delay * (2 ** (attempt - 1))
                print(f"Reconnect attempt {attempt} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)

        raise RuntimeError("Failed to reconnect to DB after retries")

    def _ensure_connected(self):
        """
        Ensure the connection is alive. Try ping(reconnect=True) first,
        otherwise recreate connection using stored params.
        """
        with self._lock:
            if self.connection is None:
                # no connection object, try to recreate
                self._recreate_connection()
                return

            try:
                # ping with reconnect True attempts to reconnect at C level if supported
                # attempts/delay are defaults; wrap in try/except
                self.connection.ping(reconnect=True, attempts=3, delay=1)
                return
            except Exception:
                # fallback: close and recreate
                try:
                    self.connection.close()
                except Exception:
                    pass
                self.connection = None
                self._recreate_connection()

    def execute(self, query, args = None):
        """
        Execute a query and return results.
        - SELECT queries -> list of tuples (cursor.fetchall())
        - Non-SELECT -> returns affected rowcount (int)
        Retries on OperationalError (connection lost) and attempts reconnect.
        This method preserves the original signature.
        """
        retries = self.default_query_retries
        backoff = self.default_query_backoff
        attempt = 0
        last_exc = None

        while attempt < retries:
            attempt += 1
            try:
                # Ensure connection is alive before creating cursor
                self._ensure_connected()

                with self._lock:
                    # create a fresh cursor for each call
                    self.cursor = self.connection.cursor()
                    try:
                        self.cursor.execute(query, args or ())
                    except Exception:
                        # ensure cursor closed on execute error
                        try:
                            self.cursor.close()
                        except Exception:
                            pass
                        raise

                    # If the cursor has rows (SELECT), fetch them
                    if self.cursor.with_rows:
                        rows = self.cursor.fetchall()
                        try:
                            self.cursor.close()
                        except Exception:
                            pass
                        return rows
                    else:
                        # Non-select: commit and return affected rows
                        try:
                            # commit may raise if connection lost; ignore here and let outer except handle
                            self.connection.commit()
                        except Exception:
                            pass
                        affected = self.cursor.rowcount
                        try:
                            self.cursor.close()
                        except Exception:
                            pass
                        return affected

            except OperationalError as oe:
                # Connection not available or lost; attempt reconnect and retry
                last_exc = oe
                print(f"OperationalError during execute: {oe}. Attempt {attempt}/{retries}. Reconnecting...")
                # clear connection so ensure_connected will recreate
                with self._lock:
                    try:
                        if self.connection:
                            self.connection.close()
                    except Exception:
                        pass
                    self.connection = None
                # exponential backoff
                time.sleep(backoff * (2 ** (attempt - 1)))
                continue
            except Error as e:
                # Other MySQL errors (syntax, constraint) should be raised immediately
                # Provide traceback for easier debugging
                print("MySQL Error during execute:", e)
                traceback.print_exc()
                raise
            except Exception as e:
                # Unexpected error
                print("Unexpected error during execute:", e)
                traceback.print_exc()
                raise

        # exhausted retries
        raise RuntimeError("Query failed after retries") from last_exc

    def close(self):
        """
        Close cursor and connection cleanly.
        """
        with self._lock:
            if hasattr(self, "cursor") and self.cursor:
                try:
                    self.cursor.close()
                except Exception as e:
                    print(f"Cursor close failed: {e}")
                finally:
                    self.cursor = None
            if hasattr(self, "connection") and self.connection:
                try:
                    try:
                        alive = getattr(self.connection, "is_connected", lambda: False)()
                    except Exception:
                        alive = False
                    try:
                        self.connection.close()
                    except Exception as e:
                        print(f"Connection close failed: {e}")
                finally:
                    self.connection = None
