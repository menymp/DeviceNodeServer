
import sys
import os
import time
import zmq
import threading
import json
from threading import Event

sys.path.append('../ConfigsUtils')
from deviceManager import deviceManager
from configsCreate import configsParser

def initMQServer(serverPath):
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(serverPath)
    return socket

def taskLoadDevices(deviceManager, timeSleep, stopEvent):
    while not stopEvent.is_set():
        deviceManager.deviceLoad()
        time.sleep(timeSleep)
    pass

def startLoadDevices(deviceManager, add_time_poll):
    stopEvent = Event()
    taskAddDevices = threading.Thread(target=taskLoadDevices, args=(deviceManager, add_time_poll, stopEvent, ))
    taskAddDevices.start()
    return taskAddDevices, stopEvent

def stopLoadDevices(stopEvent):
    stopEvent.set()
    pass

def processIncommingMessage(deviceManager, message):
    #Process Incomming message request from different processes
    #ToDo: write expected logic and cases for this data
    commandObj = json.loads(message)

    if(commandObj["method"] == "execCommand"):
        result = deviceManager.executeCMDJson(commandObj["args"])
    elif(commandObj["method"] == "executeCMDJson"):
        result = deviceManager.execCommand(commandObj["args"])
    else:
        error = {
            "type":"unknown method"
        }
        result = json.dumps(error)
    return result

if __name__ == "__main__":
    cfgObj = configsParser()
    args = cfgObj.readConfigData(os.getcwd() + "../configs.ini")
    zmqCfg = cfgObj.readSection("zmqConfigs",os.getcwd() + "../configs.ini")
    devMgrCfg = cfgObj.readSection("deviceMgr",os.getcwd() + "../configs.ini")


    deviceMgr = deviceManager()
    deviceMgr.init(args)
    taskLoadDevices, stopEvent = startLoadDevices(deviceMgr, int(devMgrCfg["add-devices-time-poll"]))
    print("device manager started...")
    mqServerObj = initMQServer(zmqCfg["device-manager-server-path"])
    print("MQ Server started at: " + MQ_DEV_MGR_SERVER_PATH)

    while(True): #Add a stop signal
        message = mqServerObj.recv()
        result = processIncommingMessage(deviceMgr, message)
        #  Send reply back to client
        mqServerObj.send(result)
        pass
    stopLoadDevices(stopEvent)
    pass