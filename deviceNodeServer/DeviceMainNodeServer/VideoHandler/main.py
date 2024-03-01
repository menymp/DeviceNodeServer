
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

from configsCreate import configsParser
from videoHttpController import videoHandler



def initMQServer():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(zmqCfg["video-handler-server-path"])
    return socket

def taskHandleIncomingMsgs(videoHandler, mqServer, stopEvent):
    while not stopEvent.is_set():
        msg = mqServer.recv().decode() ###### test plis
        result = processIncommingMessage(videoHandler, msg)
        mqServer.send(result.encode()) ##### test plis
    pass

def startHandleIncomingMsgs(videoHandler, mqServer):
    stopEvent = Event()
    taskHandleIncMsgs = threading.Thread(target=taskHandleIncomingMsgs, args=(videoHandler, mqServer, stopEvent, ))
    taskHandleIncMsgs.start()
    return taskHandleIncMsgs, stopEvent

def stopHandleIncomingMsgs(stopEvent):
    stopEvent.set()
    pass

def processIncommingMessage(videoHandler, message):
    #Process Incomming message request from different processes
    #ToDo: write expected logic and cases for this data
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
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    configs_path = os.path.join(parent_dir, 'configs.ini')
    print("configs path: " + configs_path)

    cfgObj = configsParser()
    args = cfgObj.readConfigData(configs_path)
    zmqCfg = cfgObj.readSection("zmqConfigs",configs_path)

    videoHandlerObj = videoHandler(args)
    print("video service started ...")
    mqServerObj = initMQServer()
    print("MQ Server started at: " + zmqCfg["video-handler-server-path"])

    taskHandleIncMsgs, stopEvent = startHandleIncomingMsgs(videoHandlerObj, mqServerObj)

    eventStop = Event()
    def sigterm_handler(signum, frame):
        print("stop process")
        eventStop.set()
        stopHandleIncomingMsgs(stopEvent)
        videoHandlerObj.stop()
        mqServerObj.destroy()
    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    videoHandlerObj.serverListen()
    
    pass