# event_reactor/handlers/rfid/worker.py
import os
import json
import logging
import signal
import sys
import time
from threading import Event
import paho.mqtt.client as mqtt

from os.path import dirname, realpath, sep, pardir
# Get current main.py directory
#sys.path.append(dirname(realpath(__file__)) + sep + pardir)
#sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DButils")
#sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")
sys.path.append("/app/DButils")
from DButils.dbEvents import dbRfidActions
from DButils.dbEvents import dbScriptActions

logging.basicConfig(level=os.environ.get("WORKER_LOG_LEVEL", "INFO"))
logger = logging.getLogger("rfid_worker")

# --- read common envs (provided by reactor) ---
INSTANCE_ID = os.getenv("INSTANCE_ID")
MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "mqtt-broker")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))

DB_HOST = os.getenv("DB_HOST", "nodes-db")
DB_NAME = os.getenv("DB_NAME", "")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD_FILE = os.getenv("DB_PASSWORD_FILE", "/run/secrets/db_user_password")

logger.info("instance id: " + str(INSTANCE_ID))
logger.info("host mqtt: " + str(MQTT_HOST))
logger.info("mqtt port: " + str(MQTT_PORT))
logger.info("db host: " + str(DB_HOST))
logger.info("db name: " + str(DB_NAME))
logger.info("db user: " + str(DB_USER))
logger.info("db pass: " + str(DB_PASSWORD_FILE))

STOP = Event()

'''
{
  "locks": [
    {
      "name": "front_door",
      "event_topic": "/NodeRfid1/rifd_sensor/value",
      "open_lock_topic": "/NodeRelays1/front_door_output/",
      "open_command": "OPEN"
    },
    {
      "name": "garage_door",
      "event_topic": "/NodeRfid3/rifd_sensor/value",
      "open_lock_topic": "/NodeRelays1/garage_door_output/",
      "open_command": "OPEN"
    }
  ]
}

'''

def read_secret(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return None

def fetch_config_from_db(instance_id):
    """
    Use dbEvents.dbScriptActions.get_instance(instance_id) to retrieve the row
    and parse config_json. Returns dict or None.
    """
    try:
        pw = read_secret(DB_PASSWORD_FILE)
        # import dbEvents helper
        db = dbScriptActions()
        db.initConnector(user=DB_USER, password=pw, host=DB_HOST, database=DB_NAME)
        row = db.get_instance(instance_id)
        # db.get_instance may return list/tuple/dict depending on implementation
        cfg_raw = None
        if not row:
            return None
        # handle common return shapes
        if isinstance(row, dict):
            cfg_raw = row.get("config_json")
        elif isinstance(row, (list, tuple)):
            # try to find config_json by index (common earlier code used index 6)
            try:
                cfg_raw = row[6] if len(row) > 6 else None
            except Exception:
                cfg_raw = None
        else:
            cfg_raw = None

        if not cfg_raw:
            return None
        # parse JSON if needed
        if isinstance(cfg_raw, str):
            try:
                return json.loads(cfg_raw)
            except Exception:
                logger.exception("failed to parse config_json for instance %s", instance_id)
                return None
        elif isinstance(cfg_raw, (dict, list)):
            return cfg_raw
        else:
            return None
    except Exception:
        logger.exception("failed to fetch config from DB for instance %s", instance_id)
        return None

def load_instance_config():
    """
    Priority:
      1) DB via INSTANCE_ID
      2) HANDLER_CFG_LOCKS env (legacy)
      3) mounted config file path HANDLER_CONFIG_PATH
    """
    cfg = {}
    # 1) DB
    if INSTANCE_ID:
        cfg_db = fetch_config_from_db(INSTANCE_ID)
        if cfg_db:
            logger.info("loaded config_json from DB for instance %s", INSTANCE_ID)
            return cfg_db

    # 2) HANDLER_CFG_LOCKS env (legacy)
    raw = os.getenv("HANDLER_CFG_LOCKS")
    if raw:
        try:
            # if it's a JSON string representing the whole config object
            parsed = json.loads(raw)
            logger.info("loaded config from HANDLER_CFG_LOCKS env")
            return parsed
        except Exception:
            logger.exception("failed to parse HANDLER_CFG_LOCKS env")

    # 3) mounted file
    cfg_path = os.getenv("HANDLER_CONFIG_PATH")
    if cfg_path and os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r") as f:
                parsed = json.load(f)
                logger.info("loaded config from file %s", cfg_path)
                return parsed
        except Exception:
            logger.exception("failed to read config file %s", cfg_path)

    # fallback: empty config
    logger.warning("no instance config found (DB, env, or file); continuing with empty config")
    return {}

# --- DB access abstraction: prefer dbEvents.dbRfidActions if available ---
class RfidDB:
    def __init__(self):
        self.client = None
        self.using_db_events = False

    def connect(self):
        pw = read_secret(DB_PASSWORD_FILE)
        # try to import dbEvents (preferred)
        try:
            # ensure parent paths if packaged differently
            self.client = dbRfidActions()
            # dbRfidActions inherits dbConnectorBaseSimple.initConnector(user,password,host,database)
            self.client.initConnector(user=DB_USER, password=pw, host=DB_HOST, database=DB_NAME)
            self.using_db_events = True
            logger.info("connected to DB via dbEvents.dbRfidActions")
            return
        except Exception:
            logger.debug("dbEvents not available, falling back to direct mysql connector")

        # fallback: direct mysql connector
        try:
            import mysql.connector
            self.conn = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=pw,
                database=DB_NAME,
                autocommit=True
            )
            self.cursor = self.conn.cursor(dictionary=True)
            self.using_db_events = False
            logger.info("connected to DB via mysql-connector")
        except Exception:
            logger.exception("failed to connect to DB")
            raise

    def close(self):
        try:
            if self.using_db_events and self.client:
                self.client.deinitConnector()
            else:
                if hasattr(self, "cursor"):
                    self.cursor.close()
                if hasattr(self, "conn"):
                    self.conn.close()
        except Exception:
            logger.exception("error closing DB connection")

    def get_user_by_rfid(self, rfid_id):
        """
        Return user row(s) for given rfid_id. Uses dbEvents if available, otherwise runs a simple query.
        """
        logger.info("getting user by rfid: " + str(rfid_id))
        try:
            if self.using_db_events:
                res = self.client.get_user_by_rfid(rfid_id)
                # dbEvents returns rows; keep as-is
                return res
            else:
                sql = ("SELECT u.* FROM users u "
                       "JOIN user_rfids r ON r.user_id = u.idUser "
                       "WHERE r.rfid_id = %s AND r.enabled = 1")
                self.cursor.execute(sql, (rfid_id,))
                return self.cursor.fetchall()
        except Exception:
            logger.exception("db query failed for rfid %s", rfid_id)
            return None

# --- MQTT handler and wiring ---

class RfidHandler:
    def __init__(self, locks):
        """
        locks: list of dicts with keys:
          - name
          - event_topic
          - open_lock_topic
          - open_command
        """
        self.locks = locks or []
        # map topic -> list of lock configs (support multiple locks subscribing same topic)
        self.topic_map = {}
        for l in self.locks:
            t = l.get("event_topic")
            if not t:
                continue
            self.topic_map.setdefault(t, []).append(l)

        self.db = RfidDB()
        self.mqtt = mqtt.Client()
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_message = self.on_message

    def start(self):
        try:
            self.db.connect()
        except Exception:
            logger.error("cannot start without DB connection")
            # still try to connect to mqtt and run; DB may come up later
        try:
            self.mqtt.connect(MQTT_HOST, MQTT_PORT)
        except Exception:
            logger.exception("failed to connect to MQTT broker %s:%s", MQTT_HOST, MQTT_PORT)
            # retry loop
            while not STOP.is_set():
                try:
                    time.sleep(5)
                    self.mqtt.connect(MQTT_HOST, MQTT_PORT)
                    break
                except Exception:
                    logger.exception("retrying mqtt connect")
        # subscribe will be done in on_connect
        self.mqtt.loop_start()

    def stop(self):
        try:
            self.mqtt.loop_stop()
            self.mqtt.disconnect()
        except Exception:
            pass
        try:
            self.db.close()
        except Exception:
            pass

    def on_connect(self, client, userdata, flags, rc):
        logger.info("connected to mqtt broker rc=%s", rc)
        # subscribe to all configured topics
        for topic in self.topic_map.keys():
            try:
                client.subscribe(topic)
                logger.info("subscribed to %s", topic)
            except Exception:
                logger.exception("subscribe failed for %s", topic)

    def _extract_rfid(self, payload):
        # payload may be dict or string
        if isinstance(payload, dict):
            return payload.get("id") or payload.get("rfid")
        if isinstance(payload, str):
            # try parse JSON string
            try:
                obj = json.loads(payload)
                if isinstance(obj, dict):
                    return obj.get("id") or obj.get("rfid")
            except Exception:
                pass
            # fallback: raw string is rfid
            return payload.strip()
        return None

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        raw = msg.payload.decode(errors="ignore")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = raw
        logger.debug("message on %s payload=%s", topic, payload)
        # find matching locks (exact topic match). If you need wildcard matching, extend here.
        locks = self.topic_map.get(topic, [])
        if not locks:
            logger.debug("no lock configured for topic %s", topic)
            return
        rfid = self._extract_rfid(payload)
        if not rfid:
            logger.info("no rfid found in payload on %s", topic)
            return
        # query DB
        users = None
        try:
            users = self.db.get_user_by_rfid(rfid)
        except Exception:
            logger.exception("db lookup failed for rfid %s", rfid)
            users = None
        if not users:
            logger.info("rfid %s not found or not enabled", rfid)
            return
        # if found, publish open command for each configured lock that matched
        for l in locks:
            out_topic = l.get("open_lock_topic")
            cmd = l.get("open_command", "OPEN")
            # build payload: include user info and original event
            out_payload = {
                "rfid": rfid,
                "command": cmd,
                "lock": l.get("name"),
                "user": users[0] if isinstance(users, (list, tuple)) and users else users,
                "source_topic": topic,
                "timestamp": int(time.time())
            }
            try:
                client.publish(out_topic, json.dumps(out_payload))
                logger.info("published open command to %s for rfid %s", out_topic, rfid)
            except Exception:
                logger.exception("failed to publish open command to %s", out_topic)

# --- bootstrap: read config from HANDLER_CFG_LOCKS ---
def read_instance_config():
    cfg = {}
    for k, v in os.environ.items():
        if not k.startswith("HANDLER_CFG_"):
            continue
        key = k[len("HANDLER_CFG_"):].lower()
        try:
            cfg[key] = json.loads(v)
        except Exception:
            cfg[key] = v
    return cfg

def _sigterm(signum, frame):
    logger.info("received stop signal")
    STOP.set()

signal.signal(signal.SIGTERM, _sigterm)
signal.signal(signal.SIGINT, _sigterm)

def main():
    cfg = load_instance_config()
    locks = cfg.get("locks") or []
    logger.info("starting rfid handler with %d locks", len(locks))
    handler = RfidHandler(locks)
    handler.start()
    try:
        while not STOP.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        STOP.set()
    finally:
        handler.stop()
        logger.info("rfid handler stopped")

if __name__ == "__main__":
    main()
