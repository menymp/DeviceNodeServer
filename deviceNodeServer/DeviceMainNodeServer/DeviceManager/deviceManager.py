import threading
import json
import time
import sys
import zmq
import threading
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import queue

from os.path import dirname, realpath, sep, pardir
# Get current main.py directory
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DButils")
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")

from dbActions import dbDevicesActions
from loggerUtils import get_logger
logger = get_logger(__name__)

'''
ToDo:	now that i saw again this implementation, this is not a suitable approach
        		current protocol works like:
        		the nodeDevicesDiscoveryTool read each given node and initialze the existing devices with its manifest
				and the devices table is updated in the database, then the device manager performs an initialization of
				the expected existing devices preriodicaly in the devices list. then, the front end sends the commands
				to getValue and read the current devices or to execute a command execution.
				
				this makes a complex situation where there is no way to know the true current state of the device.
				
				a better architecture should move the behavior of the command to the current device and create a dual
				channel to perform a response for each existing device
'''

#

#handle command object as an array in order to process an object
#this approach is better since a fast processing is posible by large
#objects in the backend, also one request allow the system to 
#keep the latency at minimun instead of individual requests
'''
example of response object
cmdResult = {
	"result":"24",
	"state":"OK"
}
'''
class deviceManager():
    Devices = []
    def init(self, initArgs, zmqSyncServer, mqttBroker, mqttPort = 1883, mqttKeepalive = 60):
        logger.info("init device manager with %s %s" % (initArgs, mqttBroker))
        self.dbHost = initArgs[0]
        self.dbName = initArgs[1]
        self.dbUser = initArgs[2]
        self.dbPass = initArgs[3]
        self.mqttBroker = mqttBroker
        self.mqttPort = mqttPort
        self.mqttKeepalive = mqttKeepalive
        self.dbActions = dbDevicesActions()
        self.dbActions.initConnector(self.dbUser,self.dbPass,self.dbHost,self.dbName)
        self.deviceLoad()

        # zmq client for device data sync
        self.zmqSyncServer = zmqSyncServer
        self.initZmqClient()
        pass

    def initZmqClient(self):
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.REQ)
        self.socket.connect(self.zmqSyncServer)
        pass

    def requestDeviceData(self, deviceId):
        requestString = json.dumps({ "deviceId": deviceId })
        self.socket.send_string(requestString)
        reply = self.socket.recv_string()
        if reply in [f"ERR_KEY", f"ERR_NULL", f"NOT_FOUND"]:
            logger.error("request error")
            return None
        return json.loads(reply)
        #logger.info(f"Reply: {reply}")

    # load devices from db
    def deviceLoad(self):
        logger.info("loading devices")
        self.availableDevices = self.dbActions.getDevices()
        for deviceInfo in self.availableDevices:
            if not self.deviceAlreadyInit(deviceInfo[1],deviceInfo[5]):
                logger.info("integrating new device %s" % (deviceInfo[1]))
                tmpDevice = device()
                tmpDevice.init(deviceInfo, self.requestDeviceData, self.mqttBroker, self.mqttPort, self.mqttKeepalive)
                self.Devices.append(tmpDevice)
            pass
        self.cleanOldDevices()
        # Moved cleanup to maintenance file
        pass


    def deviceAlreadyInit(self, deviceName, parentNodeId):
        flagExists = False
        for deviceObj in self.Devices:
            if (deviceObj.name == deviceName and deviceObj.idParentNode == parentNodeId):
                flagExists = True
        return flagExists
    
    def cleanOldDevices(self):
        for index, deviceObj in enumerate(self.Devices[:]):  # iterate over a copy
            flagExists = False
            for availableDevice in self.availableDevices:
                if (deviceObj.name == availableDevice[1] and deviceObj.idParentNode == availableDevice[5]):
                    flagExists = True
                    break
            if not flagExists:
                logger.info("device '%s' from parent node id '%s' removed" % (deviceObj.name, deviceObj.idParentNode))
                deviceToDel = self.Devices.pop(index)
                del deviceToDel

    def executeCMDJson(self, jsonArgs):
        logger.info("running json command %s" % (jsonArgs))
        cmdArrayObj1 = json.loads(jsonArgs["args"])
        cmdArrayObj = json.loads(cmdArrayObj1)#ToDo: fix, for some weird reason, objects are stringified with dual quotes
        results = []
        #print(cmdArrayObj)
        
        for cmd in cmdArrayObj:
            state = "SUCCESS"

            if "servercommand" in cmd:
                result = []
                try:
                    if cmd["servercommand"] == "getMeasures":
                        result = self.dbActions.getDeviceMeasures(cmd['idDevice'])
                        formattedResults = []
                        for row in result:
                            tmpFormatRow = {
                                "id": row[0],
                                "value": str(row[1]),
                                "date": row[2].strftime("%Y-%m-%d %H:%M:%S")
                            }
                            formattedResults.append(tmpFormatRow)
                    
                except:
                    logger.info("error attempting to retrive measures")
                    state = "ERROR"
                
                cmdServerResult = {
                    "idDevice":cmd['idDevice'],
                    "syscommand":cmd['servercommand'],
                    "result":json.dumps(formattedResults),
                    "state":state
                }
                results.append(cmdServerResult)
                logger.info("command results %s" % (cmdServerResult))
                continue


            try:
                result = self.executeCMDraw(cmd['idDevice'], cmd['command'], cmd['args'])
                logger.info("raw command result %s" % (result))
            except:
                state = "ERROR"

            cmdResult = {
                "idDevice":cmd['idDevice'],
                "command":cmd['command'],
                "result":result,
                "state":state
            }
            results.append(cmdResult)
        return json.dumps(results)

    def executeCMD(self, idDevice, command, args):
        logger.info("running command %s" % (idDevice, command, args))
        rawResult = self.executeCMDraw(idDevice, command, args)
        dictionary = {'result':rawResult}
        jsonString = json.dumps(dictionary, indent=4)
        logger.info("result %s" % (jsonString))
        return jsonString
    
    def executeCMDraw(self, idDevice, command, args):
        logger.info("running raw command %s" % (idDevice, command, args))
        result = ""
        for device in self.Devices:
            if device.id == idDevice:
                result = device.executeCMD(command,args)
                break
        return result
    
    #toDo: still in proof of concept expect for a better approach
    def execCommand(self, inputArgs):
        logger.info("base command %s" % (inputArgs))
        #parses the command
        #list devices
        
        inTks = inputArgs
        
        if inTks[0] == 'ls':
            ids = []
            for deviceObj in self.Devices:
                ids.append((deviceObj.name,deviceObj.id,deviceObj.type))
            return str(ids)
        elif inTks[0] == "run":
            result = self.executeCMD(inTks[1],inTks[2],inTks[3])
            return result
        else:
            logger.error("unknown")
            return "unknown command"
        pass
    
    def jsonDumpResult(self,value,key):
        pass

class device():
    def init(self, args, requestDeviceData, mqttBroker, mqttPort, mqttKeepalive):
        logger.info("init new device %s" % (args))
        self.initArgs = args
        self.mqttBroker = mqttBroker
        self.mqttPort = mqttPort
        self.mqttKeepalive = mqttKeepalive
        self.id = args[0]
        self.name = args[1]
        self.mode = args[2]
        self.type = args[3]
        self.channelPath = args[4]
        self.idParentNode = args[5]
        self.ParentNodeName = args[6]
        self.ParentNodePath = args[7]
        self.ParentNodeProtocol = args[8]
        self.idOwnerUser = args[9]
        self.ParentConnectionParameters = args[10]
        self.requestDeviceData = requestDeviceData
        self.value = ""
        self.initDriver(self.ParentNodeProtocol)
        pass

    def __del__(self):
        logger.info("exiting device")
        if self.Driver:
            self.Driver.stop()
        pass

    def getValue(self):
        result = self.requestDeviceData(self.id)
        if "Value" not in result:
            return ""
        return result["Value"]

    def initDriver(self, protocol):
        if protocol == "MQTT":
            self.Driver = mqttDriver()
            if self.mode == "PUBLISHER":
                #a publisher just updates its internal value
                self.Driver.init(self.channelPath, self.mqttBroker, self.mqttPort, self.mqttKeepalive)
            if self.mode == "SUBSCRIBER":
                #if a subscriber type, in order to get the value we subscribe to the publish path
                self.Driver.init(self.channelPath, self.mqttBroker, self.mqttPort, self.mqttKeepalive)
        else:
            raise Exception("Protocol "+protocol+" not supported")

    def executeCMD(self, cmd, args):
        logger.info("running command %s" % (cmd, args))
        result = ""
        
        if cmd == 'getValue' or self.mode == 'PUBLISHER':
            result = self.getValue()
            self.value = result
        if cmd != 'getValue' and self.mode == 'SUBSCRIBER':
            #currently the only thing that accepts commands are SUBSCRIBER nodes
            self.Driver.sendCommand(cmd, self.channelPath)
            result = "OK"
        return result

class mqttDriver():
    def init(self, deviceTopic, mqttBroker, mqttPort, mqttKeepalive):
        logger.info("starting an mqtt protocol driver %s" % (deviceTopic))
        self.deviceTopic = deviceTopic
        self.lastSentCmd = ""
        self.mqttBroker = mqttBroker
        self.mqttPort = mqttPort
        self.mqttKeepalive = mqttKeepalive

        self.client = mqtt.Client()

        # Connect to the broker (default port 1883, keepalive 60 seconds)
        self.client.connect(mqttBroker, port=mqttPort, keepalive=mqttKeepalive)
        pass

    def sendCommand(self,command):
        logger.info("sending mqtt command")
        self.lockUpdateFlag  = True
        self.lastSentCmd = command
        self.client.publish(topic = self.deviceTopic, payload = command)
        pass

    def stop(self):
        logger.info("stopping mqtt driver")
        self.client.disconnect()
        self.client.loop_stop()