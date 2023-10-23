import sys
import os
import time
import zmq
import threading
import json
from threading import Event

sys.path.append('../ConfigsUtils')
from nodeManager import nodeDeviceManager
from configsCreate import configsParser

SEARCH_DEVICES_PERIOD = 20

if __name__ == "__main__":
    cfgObj = configsParser()
    args = cfgObj.readConfigData(os.getcwd() + "../configs.ini")
    devMgr = nodeDeviceManager()
    while(True):
        devMgr.getNodes(args)
        devMgr.discoverNodeDevices()

        while devMgr.getState() != 'DONE':
            pass
        devMgr.registerNodes()
        time.sleep(SEARCH_DEVICES_PERIOD)
    pass