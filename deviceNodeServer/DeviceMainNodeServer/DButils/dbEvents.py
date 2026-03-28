'''
dbEvents.py


'''
import json
import logging
from mySqlConn import dbConn

logger = logging.getLogger(__name__)

class dbConnectorBaseSimple():
    def initConnector(self, user, password, host, database, auth='mysql_native_password'):
        self.dbConn = dbConn()
        self.dbConn.connect(user=user, password=password, host=host, database=database, auth=auth)

    def deinitConnector(self):
        try:
            self.dbConn.close()
        except Exception:
            logger.exception("Error closing DB connection")

class dbScriptActions(dbConnectorBaseSimple):
    """CRUD and runtime helpers for scripts and script_instances"""

    # --- scripts table helpers (optional) ---
    def create_script(self, name, entry_point, runtime='subprocess', description=None):
        sql = "INSERT INTO scripts (name, entry_point, runtime, description) VALUES (%s, %s, %s, %s)"
        self.dbConn.execute(sql, (name, entry_point, runtime, description))
        res = self.dbConn.execute("SELECT LAST_INSERT_ID();")
        return res[0][0]

    def get_script_by_name(self, name):
        return self.dbConn.execute("SELECT * FROM scripts WHERE name = %s", (name,))

    # --- script_instances CRUD ---
    def create_instance(self, script_id, instance_name, config_json=None,
                        start_mode='always', runtime='subprocess',
                        restart_policy=None, resources=None, enabled=1):
        cfg = json.dumps(config_json, ensure_ascii=False) if config_json is not None else None
        rp = json.dumps(restart_policy, ensure_ascii=False) if restart_policy is not None else json.dumps({"max_restarts":3,"backoff_seconds":5})
        resrc = json.dumps(resources, ensure_ascii=False) if resources is not None else None

        sql = ("INSERT INTO script_instances "
               "(script_id, instance_name, enabled, start_mode, runtime, config_json, restart_policy, resources) "
               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
        self.dbConn.execute(sql, (script_id, instance_name, enabled, start_mode, runtime, cfg, rp, resrc))
        res = self.dbConn.execute("SELECT LAST_INSERT_ID();")
        return res[0][0]

    def get_instance(self, instance_id):
        return self.dbConn.execute("SELECT * FROM script_instances WHERE id = %s", (instance_id,))

    def list_instances(self, only_enabled=False, start_mode=None):
        sql = "SELECT * FROM script_instances"
        params = []
        clauses = []
        if only_enabled:
            clauses.append("enabled = 1")
        if start_mode:
            clauses.append("start_mode = %s")
            params.append(start_mode)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        return self.dbConn.execute(sql, tuple(params) if params else None)

    def update_instance_config(self, instance_id, config_json):
        cfg = json.dumps(config_json, ensure_ascii=False)
        sql = "UPDATE script_instances SET config_json = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        return self.dbConn.execute(sql, (cfg, instance_id))

    def set_instance_enabled(self, instance_id, enabled):
        sql = "UPDATE script_instances SET enabled = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        return self.dbConn.execute(sql, (1 if enabled else 0, instance_id))

    def delete_instance(self, instance_id):
        return self.dbConn.execute("DELETE FROM script_instances WHERE id = %s", (instance_id,))

    # --- runtime bookkeeping ---
    def record_instance_start(self, instance_id):
        sql = "UPDATE script_instances SET last_start_at = CURRENT_TIMESTAMP, restarts_count = 0 WHERE id = %s"
        return self.dbConn.execute(sql, (instance_id,))

    def record_instance_exit(self, instance_id, exit_code):
        sql = "UPDATE script_instances SET last_exit_at = CURRENT_TIMESTAMP, last_exit_code = %s, restarts_count = restarts_count + 1 WHERE id = %s"
        return self.dbConn.execute(sql, (exit_code, instance_id))

    def bump_restart_count(self, instance_id):
        sql = "UPDATE script_instances SET restarts_count = restarts_count + 1 WHERE id = %s"
        return self.dbConn.execute(sql, (instance_id,))

    def reset_restart_count(self, instance_id):
        sql = "UPDATE script_instances SET restarts_count = 0 WHERE id = %s"
        return self.dbConn.execute(sql, (instance_id,))

    # helper to fetch instances that should be started at boot
    def get_instances_to_start(self):
        return self.dbConn.execute("SELECT * FROM script_instances WHERE enabled = 1 AND start_mode = 'always'")

class dbRfidActions(dbConnectorBaseSimple):
    """User <-> RFID binding helpers"""

    def add_rfid(self, user_id, rfid_id, label=None, enabled=1):
        sql = "INSERT INTO user_rfids (user_id, rfid_id, label, enabled) VALUES (%s, %s, %s, %s)"
        try:
            self.dbConn.execute(sql, (user_id, rfid_id, label, enabled))
            res = self.dbConn.execute("SELECT LAST_INSERT_ID();")
            return res[0][0]
        except Exception:
            logger.exception("Failed to add RFID binding")
            raise

    def remove_rfid(self, user_id, rfid_id):
        sql = "DELETE FROM user_rfids WHERE user_id = %s AND rfid_id = %s"
        return self.dbConn.execute(sql, (user_id, rfid_id))

    def disable_rfid(self, user_id, rfid_id):
        sql = "UPDATE user_rfids SET enabled = 0 WHERE user_id = %s AND rfid_id = %s"
        return self.dbConn.execute(sql, (user_id, rfid_id))

    def list_rfids_for_user(self, user_id):
        return self.dbConn.execute("SELECT * FROM user_rfids WHERE user_id = %s", (user_id,))

    def get_user_by_rfid(self, rfid_id):
        sql = ("SELECT u.* FROM users u "
               "JOIN user_rfids r ON r.user_id = u.idUser "
               "WHERE r.rfid_id = %s AND r.enabled = 1")
        return self.dbConn.execute(sql, (rfid_id,))

    def find_rfid(self, rfid_id):
        return self.dbConn.execute("SELECT * FROM user_rfids WHERE rfid_id = %s", (rfid_id,))
