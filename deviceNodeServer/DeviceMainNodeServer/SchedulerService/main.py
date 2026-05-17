import sys
import os
import time
import json
from threading import Event
import signal
from os.path import dirname, realpath, sep, pardir
import asyncio
import logging
from scheduler import SchedulerService
import paho.mqtt.client as mqtt

sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DButils")

from secretReader import get_secret
from loggerUtils import get_logger

from schedulerHelper import SchedulerDB

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("scheduler_main")

MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_KEEPALIVE = int(os.getenv("MQTT_CLIENT_KEEPALIVE", "60"))

def create_mqtt_client():
    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)
    client.loop_start()
    return client

async def run():
    db = SchedulerDB()
    mqtt_client = create_mqtt_client()
    svc = SchedulerService(db, mqtt_client, default_tz=os.getenv("SCHEDULER_TZ", "UTC"))
    await svc.start()

    stop_event = asyncio.Event()

    def _on_signal(sig):
        logger.info("received signal %s, shutting down", sig)
        stop_event.set()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, lambda: _on_signal('SIGTERM'))
    loop.add_signal_handler(signal.SIGINT, lambda: _on_signal('SIGINT'))

    await stop_event.wait()
    await svc.stop()
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("keyboard interrupt, exiting")
