import sys
import os
import time
import zmq
import threading
import json
from threading import Event
import signal

from os.path import dirname, realpath, sep, pardir
# Get current main.py directory
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "ConfigsUtils")
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")

from nodeManager import nodeDeviceManager
from configsCreate import configsParser
from secretReader import get_secret

if __name__ == "__main__":
    #parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    #configs_path = os.path.join(parent_dir, 'configs.ini')
    #print("configs path: " + configs_path)

    #cfgObj = configsParser()
    args = [os.getenv("DB_HOST", ""), os.getenv("DB_NAME", ""), os.getenv("DB_USER", ""), get_secret("DB_PASSWORD_FILE")]
    nodeDevMgrPeriod = int(os.getenv("SEARCH_DEVICES_PERIOD", "")) # cfgObj.readSection("nodeDeviceManager",configs_path)
    print("Device manager started with:")
    print(args)
    print(nodeDevMgrPeriod)

    devMgr = nodeDeviceManager()

    eventStop = Event()
    def sigterm_handler(signum, frame):
        print("stop process")
        eventStop.set()
        devMgr.stop()
    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    
    while not eventStop.is_set():
        devMgr.getNodes(args)
        devMgr.discoverNodeDevices()
        while devMgr.getState() != 'DONE':
            pass
        devMgr.registerNodes()
        time.sleep(nodeDevMgrPeriod)
    pass