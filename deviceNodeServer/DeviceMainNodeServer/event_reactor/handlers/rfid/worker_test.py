import time
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
##
###  Test file
###

if __name__ == "__main__":
    while True:
        print("Testing container rfid worker")
        time.sleep(2)