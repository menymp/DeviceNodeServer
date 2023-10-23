
import sys
import os
import time
import zmq
import threading
import json
from threading import Event

sys.path.append('../ConfigsUtils')
from configsCreate import configsParser
from videoHttpController import videoHandler


MQ_VIDEO_HANDLER_SERVER_PATH = "tcp://*:5556"

def initMQServer():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(MQ_VIDEO_HANDLER_SERVER_PATH)
    return socket

def taskHandleIncomingMsgs(videoHandler, mqServer, stopEvent):
    while not stopEvent.is_set():
        msg = mqServer.recv()
        result = processIncommingMessage(msg)
        mqServer.send(result)
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
    cfgObj = configsParser()
    args = cfgObj.readConfigData(os.getcwd() + "../configs.ini")

    videoHandlerObj = videoHandler(args)
    print("video service started ...")
    mqServerObj = initMQServer()
    print("MQ Server started at: " + MQ_VIDEO_HANDLER_SERVER_PATH)

    taskHandleIncMsgs, stopEvent = startHandleIncomingMsgs(videoHandlerObj, mqServerObj)
    videoHandlerObj.serverListen()
    stopHandleIncomingMsgs(stopEvent)
    pass