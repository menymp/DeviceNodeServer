
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
    # Get the absolute path of the parent directory
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    configs_path = os.path.join(parent_dir, 'configs.ini')
    print("configs path: " + configs_path)

    cfgObj = configsParser()
    args = cfgObj.readConfigData(configs_path)
    zmqCfg = cfgObj.readSection("zmqConfigs",configs_path)
    devMgrCfg = cfgObj.readSection("deviceMgr",configs_path)


    deviceMgr = deviceManager()
    deviceMgr.init(args)
    taskLoadDevices, stopEvent = startLoadDevices(deviceMgr, int(devMgrCfg["add-devices-time-poll"]))
    print("device manager started...")
    mqServerObj = initMQServer(zmqCfg["device-manager-server-path"])
    print("MQ Server started at: " + parent_dir)

    while(True): # ToDo: Add a stop signal
        message = mqServerObj.recv()
        result = processIncommingMessage(deviceMgr, message)
        #  Send reply back to client
        mqServerObj.send(result)
        pass
    stopLoadDevices(stopEvent)
    pass