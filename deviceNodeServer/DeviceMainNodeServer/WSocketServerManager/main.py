import sys
import os
import time
import zmq
import threading
import json
from threading import Event

sys.path.append('../ConfigsUtils')
from websocketHandler import wSocketServerManager
from configsCreate import configsParser

WEB_SOCKET_PORT = 8112
MQ_DEV_MGR_SERVER_PATH = "tcp://*:5555" #NOTE: Shared with DeviceManager, add to configs.ini

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
        self.socket.send(cmdObj)
        return self.socket.recv()
    
    def disconnect(self):
        self.socket.close()


if __name__ == "__main__":
    cfgObj = configsParser()
    args = cfgObj.readConfigData(os.getcwd() + "../configs.ini")

    onMsgHandler = handleOnMessage(MQ_DEV_MGR_SERVER_PATH)
    onMsgHandler.connect()

    WSServer = wSocketServerManager()
    WSServer.init(WEB_SOCKET_PORT)
    WSServer.serverListen(onMsgHandler.on_MessageCmd)
    onMsgHandler.disconnect()


