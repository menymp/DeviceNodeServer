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

from telegramCommands import TelegramCommandExecutor
from configsCreate import configsParser
from secretReader import get_secret
from loggerUtils import get_logger
logger = get_logger(__name__)

class handleOnCmd():
    def __init__(self, zmqPath):
        context = zmq.Context()
        #  Socket to talk to server
        logger.info("Connecting to "+ zmqPath +" server")
        self.socket = context.socket(zmq.REQ)
        self.zmqPath = zmqPath
        pass

    def connect(self):
        self.socket.connect(self.zmqPath)
        logger.info("succesfuly connected to " + self.zmqPath)

    def execCommand(self, cmdObj):
        #deviceManager.executeCMDJson
        #command form:
        logger.info("running command " + str(cmdObj))
        
        cmd = {
            "method":"executeCMDJson",
            "args":cmdObj
        }
        
        self.socket.send(json.dumps(cmd).encode())
        return self.socket.recv().decode()
    
    def disconnect(self):
        self.socket.close()
        logger.info("disconected from " + self.zmqPath)

if __name__ == "__main__":
    #parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    #configs_path = os.path.join(parent_dir, 'configs.ini')
    #print("configs path: " + configs_path)

    #cfgObj = configsParser()
    args = [os.getenv("DB_HOST", ""), os.getenv("DB_NAME", ""), os.getenv("DB_USER", ""), get_secret("DB_PASSWORD_FILE")] # [argsP["host"],argsP["dbname"],argsP["user"],argsP["pass"],argsP["broker"]]
    zmqDeviceManager = os.getenv("DEVICE_MANAGER_LOCAL_CONN", "")
    zmqVideoHandler = os.getenv("VIDEO_HANDLER_LOCAL_CONN", "")
    logger.info("Telegram Executor started with:")
    logger.info(args)
    logger.info(zmqDeviceManager)
    logger.info(zmqVideoHandler)

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
        logger.info("stop process")
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