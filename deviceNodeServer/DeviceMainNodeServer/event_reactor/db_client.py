
"""
db_client.py

Thin adapter that uses dbEvents.dbScriptActions to interact with script_instances.
No SQL here; dbEvents provides the interface.
"""
import sys
import logging

from os.path import dirname, realpath, sep, pardir
# Get current main.py directory
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DButils")
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")
from dbEvents import dbScriptActions

logger = logging.getLogger("db_client")

class DBClient:
    def __init__(self, user=None, password=None, host=None, database=None):
        self._db = dbScriptActions()
        # caller must call init_connector with secrets from env
        self._connected = False

    def init_connector(self, user, password, host, database):
        self._db.initConnector(user=user, password=password, host=host, database=database)
        self._connected = True

    def close(self):
        try:
            if self._connected:
                self._db.deinitConnector()
        except Exception:
            logger.exception("error closing db client")

    def get_instances_to_start(self):
        return self._db.get_instances_to_start()

    def record_start(self, instance_id):
        try:
            return self._db.record_instance_start(instance_id)
        except Exception:
            logger.exception("record_instance_start failed for %s", instance_id)

    def record_exit(self, instance_id, exit_code):
        try:
            return self._db.record_instance_exit(instance_id, exit_code)
        except Exception:
            logger.exception("record_instance_exit failed for %s", instance_id)

    def disable_instance(self, instance_id):
        try:
            return self._db.set_instance_enabled(instance_id, 0)
        except Exception:
            logger.exception("disable_instance failed for %s", instance_id)
