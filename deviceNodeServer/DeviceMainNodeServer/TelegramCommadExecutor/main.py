import sys
import os
import time
import zmq
import threading
import json
from threading import Event

from os.path import dirname, realpath, sep, pardir
# Get current main.py directory
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "ConfigsUtils")

from telegramCommands import TelegramCommandExecutor
from configsCreate import configsParser


class handleOnCmd():
    def __init__(self, zmqPath):
        context = zmq.Context()
        #  Socket to talk to server
        print("Connecting to "+ zmqPath +" server")
        self.socket = context.socket(zmq.REQ)
        self.zmqPath = zmqPath
        pass

    def connect(self):
        self.socket.connect(self.zmqPath)
        print("succesfuly connected to " + self.zmqPath)

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
        print("disconected from " + self.zmqPath)

if __name__ == "__main__":
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    configs_path = os.path.join(parent_dir, 'configs.ini')
    print("configs path: " + configs_path)

    cfgObj = configsParser()
    args = cfgObj.readConfigData(configs_path)
    zmqCfg = cfgObj.readSection("zmqConfigs",configs_path)

    devMgrProxy = handleOnCmd(zmqCfg["device-manager-local-conn"])
    devMgrProxy.connect()
    videoHandlerProxy = handleOnCmd(zmqCfg["video-handler-local-conn"])
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
    #ToDo: add proper signal killers to every process in order for the server to stop execution
    while True:
        pass
    devMgrProxy.disconnect()
    videoHandlerProxy.disconnect()