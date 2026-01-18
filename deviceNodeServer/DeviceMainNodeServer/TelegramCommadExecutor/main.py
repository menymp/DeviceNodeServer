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
        
        cmd = {
            "method":"executeCMDJson",
            "args":cmdObj
        }
        
        self.socket.send(json.dumps(cmd).encode())
        return self.socket.recv().decode()
    
    def disconnect(self):
        self.socket.close()
        print("disconected from " + self.zmqPath)

if __name__ == "__main__":
    #parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    #configs_path = os.path.join(parent_dir, 'configs.ini')
    #print("configs path: " + configs_path)

    #cfgObj = configsParser()
    args = [os.getenv("DB_HOST", ""), os.getenv("DB_NAME", ""), os.getenv("DB_USER", ""), os.getenv("DB_PASSWORD_FILE", "")] # [argsP["host"],argsP["dbname"],argsP["user"],argsP["pass"],argsP["broker"]]
    zmqDeviceManager = os.getenv("DEVICE_MANAGER_LOCAL_CONN", "")
    zmqVideoHandler = os.getenv("VIDEO_HANDLER_LOCAL_CONN", "")
    print("Telegram Executor started with:")
    print(args)
    print(zmqDeviceManager)
    print(zmqVideoHandler)

    devMgrProxy = handleOnCmd(zmqDeviceManager)
    devMgrProxy.connect()
    videoHandlerProxy = handleOnCmd(zmqVideoHandler)
    videoHandlerProxy.connect()
    
    objInstances = {
    	"devices":devMgrProxy,
    	"cameras":videoHandlerProxy
    }
    objTelegramServer = TelegramCommandExecutor(args, objInstances)
    objTelegramServer.fetchUserTokens()
    objTelegramServer.start()

    eventStop = Event()
    def sigterm_handler(signum, frame):
        print("stop process")
        eventStop.set()
        objTelegramServer.stop()
        devMgrProxy.disconnect()
        videoHandlerProxy.disconnect()
    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)
    #expect a better approach since its not suitable to add every device each thread
    #   UPDATE: a better approach was adopted to split in different processes and couple
    #   with a lose communication system, in this case zmq
    
    while not eventStop.is_set():
        pass