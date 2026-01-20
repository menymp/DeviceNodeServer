
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

from deviceManager import deviceManager
from configsCreate import configsParser
from secretReader import get_secret

def initMQServer(serverPath):
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(serverPath)
    return socket

def taskLoadDevices(deviceManager, timeSleep, stopEvent):
    try:
        while not stopEvent.is_set():
            deviceManager.deviceLoad()
            time.sleep(timeSleep)
    except:
        print("conflict attempting to load devices")
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
    commandObj = json.loads(message)
    try:
        if(commandObj["method"] == "executeCMDJson"):
            result = deviceManager.executeCMDJson(commandObj)
        elif(commandObj["method"] == "executeCommand"):
            result = deviceManager.execCommand(commandObj)
        else:
            error = {
                "type":"unknown method"
            }
            result = json.dumps(error)
    except Exception as e:
        print(commandObj)
        print("command error!" + str(e))
        error = {
            "type":"command error!"
        }
        result = json.dumps(error)
    return result

if __name__ == "__main__":
    
    # Get the absolute path of the parent directory
    # parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    # configs_path = os.path.join(parent_dir, 'configs.ini')
    # print("configs path: " + configs_path)

    #cfgObj = configsParser()
    args = [os.getenv("DB_HOST", ""), os.getenv("DB_NAME", ""), os.getenv("DB_USER", ""), get_secret("DB_PASSWORD_FILE")]
    zmqDeviceManagerServerPath = os.getenv("DEVICE_MANAGER_SERVER_PATH", "")
    addDevicesTimePoll = int(os.getenv("ADD_DEVICES_TIME_POLL", ""))

    print("DeviceManager started with:")
    print(args)
    print(zmqDeviceManagerServerPath)
    print(addDevicesTimePoll)

    deviceMgr = deviceManager()
    deviceMgr.init(args)
    taskLoadDevices, stopEvent = startLoadDevices(deviceMgr, addDevicesTimePoll)
    print("device manager started...")
    mqServerObj = initMQServer(zmqDeviceManagerServerPath)
    print("MQ Server started")

    eventStop = Event()
    def sigterm_handler(signum, frame):
        print("stop process")
        eventStop.set()
        mqServerObj.destroy()
    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)
    #signal.signal(signal.SIGQUIT, sigterm_handler)

    while not stopEvent.is_set():
        message = mqServerObj.recv().decode()
        result = processIncommingMessage(deviceMgr, message)
        #  Send reply back to client
        mqServerObj.send(result.encode())
        pass
    stopLoadDevices(stopEvent)
    
    print("exit success for DeviceManager")
    pass