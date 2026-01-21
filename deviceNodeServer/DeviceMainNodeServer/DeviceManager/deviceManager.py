import threading
import json
import time
import sys
import threading
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import queue

from os.path import dirname, realpath, sep, pardir
# Get current main.py directory
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DBUtils")
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")

from dbActions import dbDevicesActions
from loggerUtils import get_logger
logger = get_logger(__name__)

#
class deviceManager():
    Devices = []
    def init(self, initArgs):
        logger.info("init device manager with %s" % initArgs)
        self.dbHost = initArgs[0]
        self.dbName = initArgs[1]
        self.dbUser = initArgs[2]
        self.dbPass = initArgs[3]
        self.dbActions = dbDevicesActions()
        self.dbActions.initConnector(self.dbUser,self.dbPass,self.dbHost,self.dbName)
        self.deviceLoad()
        self.measuresQueue = queue.Queue(10)
        self.taskWriteMeasures = threading.Thread(target=self.updateMeasuresWorker, args=())
        self.taskWriteMeasures.start()
        pass

    def updateMeasuresWorker(self):
        logger.info("measures worker starting")
        self.dbActionMeasures = dbDevicesActions()
        self.dbActionMeasures.initConnector(self.dbUser,self.dbPass,self.dbHost,self.dbName)
        while True:
            if not self.measuresQueue.empty():
                logger.info("taking measures")
                (value, idDevice) = self.measuresQueue.get()
                self.dbActionMeasures.addDeviceMeasure(value, idDevice)
        pass
    #
    def deviceLoad(self):
        logger.info("loading devices")
        self.availableDevices = self.dbActions.getDevices()
        for deviceInfo in self.availableDevices:
            if not self.deviceAlreadyInit(deviceInfo[1],deviceInfo[5]):
                logger.info("integrating new device %s" % deviceInfo)
                tmpDevice = device()
                tmpDevice.init(deviceInfo, self.updateDeviceMeasure)
                self.Devices.append(tmpDevice)
            pass
        self.cleanOldDevices()
        # Moved cleanup to maintenance file
        pass

    def updateDeviceMeasure(self, value, idDevice):
        try:
            logger.info("new measure for %s" % (value, idDevice))
            self.measuresQueue.put((value, idDevice))
        except Exception as e:
            print("Error attempting to update '" + str(idDevice) + "' device with '"+ str(value) +"' value")
        pass


    def deviceAlreadyInit(self, deviceName, parentNodeId):
        flagExists = False
        for deviceObj in self.Devices:
            if (deviceObj.name == deviceName and deviceObj.idParentNode == parentNodeId):
                flagExists = True
        return flagExists
    
    def cleanOldDevices(self):
        for index, deviceObj in enumerate(self.Devices):
            flagExists = False
            for availableDevice in self.availableDevices:
                if (deviceObj.name == availableDevice[1] and deviceObj.idParentNode == availableDevice[5]):
                    flagExists = True
            if not flagExists:
                logger.info("device: '"+str(deviceObj.name)+"' from parent node id: '"+str(deviceObj.idParentNode)+ "' removed")
                print("device: '"+str(deviceObj.name)+"' from parent node id: '"+str(deviceObj.idParentNode)+ "' removed")
                deviceToDel = self.Devices.pop(index)
                del deviceToDel
        return flagExists
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
    def executeCMDJson(self, jsonArgs):
        logger.info("running json command %s" % jsonArgs)
        flagUpdate = False
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
                logger.info("command results %s" % cmdServerResult)
                continue


            try:
                result, flagUpdate = self.executeCMDraw(cmd['idDevice'], cmd['command'], cmd['args'])
                logger.info("raw command result %s" % (result, flagUpdate))
            except:
                state = "ERROR"
            
            if flagUpdate:
                state = "UPDATING" #If a write operation is performed this notify the front end

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
        rawResult, flagUpdate = self.executeCMDraw(idDevice, command, args)
        dictionary = {'result':rawResult}
        jsonString = json.dumps(dictionary, indent=4)
        logger.info("result %s" % (jsonString, flagUpdate))
        return jsonString, flagUpdate 
    
    def executeCMDraw(self, idDevice, command, args):
        logger.info("running raw command %s" % (idDevice, command, args))
        result = ""
        flagUpdate = False
        for device in self.Devices:
            if device.id == idDevice:
                result, flagUpdate = device.executeCMD(command,args)
                break
        return result, flagUpdate
    
    #toDo: still in proof of concept expect for a better approach
    def execCommand(self, inputArgs):
        logger.info("base command %s" % inputArgs)
        #parses the command
        #list devices
        
        inTks = inputArgs
        
        if inTks[0] == 'ls':
            ids = []
            for deviceObj in self.Devices:
                ids.append((deviceObj.name,deviceObj.id,deviceObj.type))
            return str(ids)
        elif inTks[0] == "run":
            result,flagUpdate = self.executeCMD(inTks[1],inTks[2],inTks[3])
            return result
        else:
            logger.error("unknown")
            return "unknown command"
        pass
    
    def jsonDumpResult(self,value,key):
        pass



class device():
    def init(self, args, updateDeviceMeasure):
        logger.info("init new device %s" % args)
        self.initArgs = args
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
        self.updateDeviceMeasure = updateDeviceMeasure

        self.value = ""
        self.initDriver(self.ParentNodeProtocol)
        pass

    def writeDeviceMeasure(self, value):
        logger.info("device update measure %s" % (value, self.id))
        self.updateDeviceMeasure(value, self.id) #adds id from device
        pass

    def __del__(self):
        logger.info("exiting device")
        if self.Driver:
            self.Driver.stop()
        pass

    def getValue(self):
        logger.info("returning value %s" % self.value)
        return self.value

    def initDriver(self, protocol):
        if protocol == "MQTT":
            self.Driver = mqttDriver()
            if self.mode == "PUBLISHER":
                #a publisher just updates its internal value
                self.Driver.init(self.ParentConnectionParameters, self.writeDeviceMeasure, self.channelPath)
            if self.mode == "SUBSCRIBER":
                #if a subscriber type, in order to get the value we subscribe to the publish path
                self.Driver.init(self.ParentConnectionParameters, self.ParentNodePath + self.name)
        else:
            raise Exception("Protocol "+args[4]+"not supported")

    def executeCMD(self, cmd, args):
        logger.info("running command %s" % (cmd, args))
        result = ""
        updatingLock = False
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
        
        if cmd == 'getValue' or self.mode == 'PUBLISHER':
            result = self.Driver.getValue()
            self.value = result
        if cmd != 'getValue' and self.mode == 'SUBSCRIBER':
            #currently the only thing that accepts commands are SUBSCRIBER nodes
            self.Driver.sendCommand(cmd, self.channelPath)
            result = "OK"
        updatingLock = self.Driver.getLockFlag()
        return result, updatingLock

class mqttDriver():
    def init(self, args, writeMeasureCallback, path = ""):
        logger.info("starting an mqtt protocol driver %s" % (args, path))
        self.subscriberPath = path
        self.connArgs = json.loads(args)
        self.initDriver()
        self.value = ""
        self.lastSentCmd = ""
        self.lockUpdateFlag = False
        self.writeMeasureCallback = writeMeasureCallback
        #self.initDriver()
        pass

    def stop(self):
        logger.info("stopping mqtt driver")
        self.client.disconnect()
        self.client.loop_stop()
        pass
    #locks the result until a new response is sent
    #since the backend is designed in this way this should
    #mitigate the effect of the delayed update
    def getLockFlag(self):
        logger.info("lock is %s" % self.lockUpdateFlag)
        return self.lockUpdateFlag

    def initDriver(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.connArgs["broker"], self.connArgs["port"], self.connArgs["keepalive"])

        taskListen = threading.Thread(target=self.clientlisten, args=(self.client,))
        taskListen.start()
        logger.info("mqtt driver thread started")
        pass

    def clientlisten(self, arg):
        arg.loop_forever()
        pass

    def sendCommand(self,command, args):
        logger.info("sending mqtt command")
        self.lockUpdateFlag  = True
        self.lastSentCmd = command
        publish.single(topic = args, payload = command, hostname = self.connArgs["broker"])
        pass

    def getValue(self):
        return self.value

    def on_connect(self, client, userdata, flags, rc):
        if self.subscriberPath == "":
            return
        self.client.subscribe(self.subscriberPath)
        pass

    def on_message(self, client, userdata, msg):
        m_decode=str(msg.payload.decode("utf-8","ignore"))
        data = json.loads(m_decode)
        logger.info("mqtt message received %s" % (client, userdata, msg))
        self.value = data["Value"]
        self.writeMeasureCallback(data["Value"]) #updates value to measures
        if self.lockUpdateFlag and self.lastSentCmd == self.value: #ToDo: a race condition may happens if no update received
            self.lockUpdateFlag = False
        pass