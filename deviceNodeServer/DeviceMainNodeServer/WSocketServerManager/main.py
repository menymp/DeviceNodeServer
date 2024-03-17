#!/usr/bin/python
import sys
import os
from os.path import dirname, realpath, sep, pardir
import time
import zmq
import threading
import json
from threading import Event
import signal

# Get current main.py directory
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "ConfigsUtils")

from websocketHandler import wSocketServerManager
from configsCreate import configsParser

class handleOnMessage():
    def __init__(self, zmqPath):
        context = zmq.Context()
        #  Socket to talk to server
        print("Connecting to DeviceManager server")
        self.socket = context.socket(zmq.REQ)
        self.zmqPath = zmqPath
        pass

    def connect(self):
        self.socket.connect(self.zmqPath)

    def on_MessageCmd(self, cmdObj):
        #deviceManager.executeCMDJson
        #command form:
        '''
        cmd = {
            "method":"executeCMDJson",
            "arg":"{json command obj ...}"
        }
        '''
        cmd = {
            "method":"executeCMDJson",
            "args":cmdObj
        }
        #print("encoded command " + str(cmd))
        self.socket.send(json.dumps(cmd).encode())
        return self.socket.recv().decode()
    
    def disconnect(self):
        self.socket.close()


if __name__ == "__main__":
    cfgObj = configsParser()
    # Get the absolute path of the parent directory
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    configs_path = os.path.join(parent_dir, 'configs.ini')
    print("configs path: " + configs_path)
    args = cfgObj.readConfigData(configs_path)
    wSockCfg = cfgObj.readSection("wSocketServerManager",configs_path)
    zmqCfg = cfgObj.readSection("zmqConfigs",configs_path)
    print(zmqCfg["device-manager-server-path"])

    onMsgHandler = handleOnMessage(zmqCfg["device-manager-local-conn"])
    onMsgHandler.connect()

    WSServer = wSocketServerManager()
    eventStop = Event()
    def sigterm_handler(signum, frame):
        print("stop process")
        eventStop.set()
        WSServer.stop()
        onMsgHandler.disconnect()
    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    WSServer = wSocketServerManager()
    WSServer.init(wSockCfg["port"])
    WSServer.serverListen(onMsgHandler.on_MessageCmd)
    onMsgHandler.disconnect()


