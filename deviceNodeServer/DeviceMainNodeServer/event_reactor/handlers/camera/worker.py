# event_reactor/handlers/camera/worker.py
import os
import time
import json
import logging
from datetime import datetime
import cv2
import numpy as np
import requests
import paho.mqtt.client as mqtt

# DButils package imports (DButils must be a package)
from DButils.dbEvents import dbScriptActions

logging.basicConfig(level=os.environ.get("WORKER_LOG_LEVEL", "INFO"))
logger = logging.getLogger("camera_worker")

# Configuration from env or config_json (reactor will pass instance config via env or DB)
INSTANCE_ID = int(os.environ.get("INSTANCE_ID", "0"))
DB_HOST = os.environ.get("DB_HOST", "nodes-db")
DB_NAME = os.environ.get("DB_NAME", "mechlabenviroment")
DB_USER = os.environ.get("DB_USER", "web_client")
DB_PASSWORD_FILE = os.environ.get("DB_PASSWORD_FILE", "/run/secrets/db_user_password")
MQTT_HOST = os.environ.get("MQTT_BROKER_HOST", "mqtt-broker")
MQTT_PORT = int(os.environ.get("MQTT_BROKER_PORT", "1883"))

# Default runtime config (will be merged with DB config)
DEFAULT_CFG = {
    "url": "http://192.168.1.16:8089/feed/mycapture.jpg",
    "mqtt_topic": "/cameras/frontdoor/motion",
    "sensitivity": 30,   # threshold area or sensitivity tuning
    "poll_interval": 1.0,
    "last_event": None
}

def read_secret(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        logger.exception("failed to read secret %s", path)
        return None

def fetch_image_bytes(url, timeout=5):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.content

def decode_image(img_bytes):
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img

def detect_motion(prev_gray, cur_gray, sensitivity):
    # compute absolute difference and threshold
    diff = cv2.absdiff(prev_gray, cur_gray)
    _, th = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    # dilate to fill holes
    kernel = np.ones((3,3), np.uint8)
    th = cv2.dilate(th, kernel, iterations=2)
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # compute total area of contours
    total_area = sum(cv2.contourArea(c) for c in contours)
    return total_area, contours

def publish_mqtt(client, topic, payload):
    try:
        client.publish(topic, json.dumps(payload))
        logger.info("published mqtt event to %s: %s", topic, payload)
    except Exception:
        logger.exception("mqtt publish failed")

def update_instance_last_event(db_actions, instance_id, cfg, event):
    try:
        # fetch current instance row (if needed)
        # merge last_event into config_json
        cfg['last_event'] = event
        db_actions.update_instance_config(instance_id, cfg)
        logger.info("updated instance %s config_json with last_event", instance_id)
    except Exception:
        logger.exception("failed to update instance config")

def main():
    # read DB password
    db_password = read_secret(DB_PASSWORD_FILE)
    if not db_password:
        logger.error("DB password not available; exiting")
        return

    # instantiate DB helper and connect
    db_actions = dbScriptActions()
    try:
        db_actions.initConnector(DB_USER, db_password, DB_HOST, DB_NAME)
    except Exception:
        logger.exception("DB connector init failed")
        return

    # load runtime config from DB (if instance exists)
    cfg = DEFAULT_CFG.copy()
    try:
        row = db_actions.get_instance(INSTANCE_ID)
        if row:
            # row[0] is the DB row tuple; config_json is at the column index used in your schema
            # adapt this extraction to your schema: assume config_json is at index 6 (example)
            # safer approach: fetch via SQL in dbScriptActions if available
            instance = row[0]
            # attempt to parse config_json if present
            # here we assume db_actions.get_instance returns list of tuples and config_json is at position 6
            config_json = instance[6] if len(instance) > 6 else None
            if config_json:
                try:
                    parsed = json.loads(config_json)
                    cfg.update(parsed)
                except Exception:
                    logger.exception("failed to parse config_json")
    except Exception:
        logger.exception("failed to read instance config; continuing with defaults")

    # setup MQTT
    mqtt_client = mqtt.Client()
    try:
        mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
    except Exception:
        logger.exception("failed to connect to mqtt broker")
        # continue; publish attempts will fail

    prev_gray = None
    last_publish_time = 0
    poll_interval = float(cfg.get("poll_interval", 1.0))
    sensitivity = float(cfg.get("sensitivity", 30))

    while True:
        try:
            img_bytes = fetch_image_bytes(cfg["url"], timeout=5)
            img = decode_image(img_bytes)
            if img is None:
                logger.warning("failed to decode image from %s", cfg["url"])
                time.sleep(poll_interval)
                continue

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21,21), 0)

            if prev_gray is None:
                prev_gray = gray
                time.sleep(poll_interval)
                continue

            total_area, contours = detect_motion(prev_gray, gray, sensitivity)
            logger.debug("motion area=%s", total_area)

            # simple threshold: if total_area > sensitivity => motion
            if total_area > sensitivity:
                now = datetime.utcnow().isoformat() + "Z"
                event = {
                    "timestamp": now,
                    "url": cfg["url"],
                    "topic": cfg["mqtt_topic"],
                    "motion_area": total_area,
                    "contours": len(contours)
                }
                # publish
                publish_mqtt(mqtt_client, cfg["mqtt_topic"], event)
                # update DB config_json with last_event
                update_instance_last_event(db_actions, INSTANCE_ID, cfg, event)
                # small cooldown to avoid spamming
                last_publish_time = time.time()
                time.sleep(max(1.0, poll_interval))
            else:
                time.sleep(poll_interval)

            prev_gray = gray
        except requests.RequestException:
            logger.exception("failed to fetch image; retrying")
            time.sleep(poll_interval)
        except Exception:
            logger.exception("unexpected error in main loop")
            time.sleep(poll_interval)

if __name__ == "__main__":
    main()
