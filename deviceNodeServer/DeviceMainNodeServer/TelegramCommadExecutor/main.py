import sys
import os
import time
import zmq
import threading
import json
from threading import Event

sys.path.append('../ConfigsUtils')
from telegramCommands import TelegramCommandExecutor
from configsCreate import configsParser


class handleOnCmd():
    def __init__(self, zmqPath):
        context = zmq.Context()
        #  Socket to talk to server
        print("Connecting to DeviceManager server")
        self.socket = context.socket(zmq.REQ)
        self.zmqPath = zmqPath
        pass

    def connect(self):
        self.socket.connect(self.zmqPath)

    def execCommand(self, cmdObj):
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
    zmqCfg = cfgObj.readSection("zmqConfigs",os.getcwd() + "../configs.ini")

    devMgrProxy = handleOnCmd(zmqCfg["device-manager-server-path"])
    devMgrProxy.connect()
    videoHandlerProxy = handleOnCmd(zmqCfg["video-handler-server-path"])
    videoHandlerProxy.connect()
    
    objInstances = {
    	"devices":devMgrProxy,
    	"cameras":videoHandlerProxy
    }
    objTelegramServer = TelegramCommandExecutor(args, objInstances)
    objTelegramServer.fetchUserTokens()
    #expect a better approach since its not suitable to add every device each thread
    #   UPDATE: a better approach was adopted to split in different processes and couple
    #   with a lose communication system, in this case zmq
    objTelegramServer.start()
    devMgrProxy.disconnect()
    videoHandlerProxy.disconnect()