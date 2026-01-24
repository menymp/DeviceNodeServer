
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

from configsCreate import configsParser
from videoHttpController import videoHandler
from secretReader import get_secret
from loggerUtils import get_logger
logger = get_logger(__name__)

#ToDo:  for now we are creating a thread to read for each vide source, is there a way to optimize this to
#       instead use a pool or load everithing on demand?

def initMQServer(zmqCfg):
    logger.info("video handler init mq server with: " + str(zmqCfg))
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(zmqCfg)
    return socket

def taskHandleIncomingMsgs(videoHandler, mqServer, stopEvent):
    while not stopEvent.is_set():
        msg = mqServer.recv().decode() ###### test plis
        logger.info("video handler new message arrived with: " + str(msg))
        result = processIncommingMessage(videoHandler, msg)
        logger.info("result: " + str(result))
        mqServer.send(result.encode()) ##### test plis
    pass

def startHandleIncomingMsgs(videoHandler, mqServer):
    stopEvent = Event()
    taskHandleIncMsgs = threading.Thread(target=taskHandleIncomingMsgs, args=(videoHandler, mqServer, stopEvent, ))
    taskHandleIncMsgs.start()
    logger.info("started video handle messages service with success")
    return taskHandleIncMsgs, stopEvent

def stopHandleIncomingMsgs(stopEvent):
    logger.info("stopping service video handler")
    stopEvent.set()
    pass

def processIncommingMessage(videoHandler, message):
    #Process Incomming message request from different processes
    commandObj = json.loads(message)

    if(commandObj["method"] == "execCommand"):
        result = videoHandler.executeCMDJson(commandObj["args"])
    else:
        error = {
            "type":"unknown method"
        }
        result = json.dumps(error)
    return result

if __name__ == "__main__":
    # Get the absolute path of the parent directory
    # parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    # configs_path = os.path.join(parent_dir, 'configs.ini')
    # print("configs path: " + configs_path)

    # cfgObj = configsParser()

    args = [os.getenv("DB_HOST", ""), os.getenv("DB_NAME", ""), os.getenv("DB_USER", ""), get_secret("DB_PASSWORD_FILE")] # [argsP["host"],argsP["dbname"],argsP["user"],argsP["pass"],argsP["broker"]]
    zmqCfgConn = os.getenv("VIDEO_HANDLER_SERVER_PATH", "")
    videoPort = int(os.getenv("VIDEO_SEED_PORT", ""))
    logger.info("Configs received for video handler:")
    logger.info(args)
    logger.info(zmqCfgConn)
    logger.info(videoPort)

    videoHandlerObj = videoHandler(args)
    logger.info("video service started ...")
    mqServerObj = initMQServer(zmqCfgConn)
    logger.info("MQ Server started at: " + zmqCfgConn)

    taskHandleIncMsgs, stopEvent = startHandleIncomingMsgs(videoHandlerObj, mqServerObj)

    eventStop = Event()
    def sigterm_handler(signum, frame):
        logger.info("stop process")
        eventStop.set()
        stopHandleIncomingMsgs(stopEvent)
        videoHandlerObj.stop()
        mqServerObj.destroy()
    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    videoHandlerObj.serverListen(videoPort)
    
    pass