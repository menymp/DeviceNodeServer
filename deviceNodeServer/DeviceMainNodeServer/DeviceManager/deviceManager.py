import threading
import json
import time
import sys
import threading
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

from os.path import dirname, realpath, sep, pardir
# Get current main.py directory
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DBUtils")

from dbActions import dbDevicesActions

#
class deviceManager():
    Devices = []
    def init(self, initArgs):
        self.dbHost = initArgs[0]
        self.dbName = initArgs[1]
        self.dbUser = initArgs[2]
        self.dbPass = initArgs[3]
        self.deviceArgs = initArgs[4]
        self.deviceLoad()
        pass
    #
    def deviceLoad(self):
        self.dbActions = dbDevicesActions()
        self.dbActions.initConnector(self.dbUser,self.dbPass,self.dbHost,self.dbName)
        self.availableDevices = self.dbActions.getDevices()
        for deviceInfo in self.availableDevices:
            if not self.deviceAlreadyInit(deviceInfo[1],deviceInfo[5]):
                tmpDevice = device()
                tmpDevice.init(deviceInfo)
                self.Devices.append(tmpDevice)
            pass
        pass

    def deviceAlreadyInit(self, deviceName, parentNodeId):
        flagExists = False
        for deviceObj in self.Devices:
            if (deviceObj.name == deviceName and deviceObj.idParentNode == parentNodeId):
                flagExists = True
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
        flagUpdate = False
        cmdArrayObj1 = json.loads(jsonArgs["args"])
        cmdArrayObj = json.loads(cmdArrayObj1)#ToDo: fix, for some weird reason, objects are stringified with dual quotes
        results = []
        #print(cmdArrayObj)
        
        for cmd in cmdArrayObj:
            state = "SUCCESS"
            try:
                result, flagUpdate = self.executeCMDraw(cmd['idDevice'], cmd['command'], cmd['args'])
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
        rawResult, flagUpdate = self.executeCMDraw(idDevice, command, args)
        dictionary = {'result':rawResult}
        jsonString = json.dumps(dictionary, indent=4)
        return jsonString, flagUpdate 
    
    def executeCMDraw(self, idDevice, command, args):
        result = ""
        flagUpdate = False
        for device in self.Devices:
            if device.id == idDevice:
                result, flagUpdate = device.executeCMD(command,args)
                break
        return result, flagUpdate
    
    #toDo: still in proof of concept expect for a better approach
    def execCommand(self, inputArgs):
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
            return "unknown command"
        pass
    
    def jsonDumpResult(self,value,key):
        pass



class device():
    def init(self, args):
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

        self.value = ""
        self.initDriver(self.ParentNodeProtocol)
        pass

    def getValue(self):
        return self.value

    def initDriver(self, protocol):
        if protocol == "MQTT":
            self.Driver = mqttDriver()
            if self.mode == "PUBLISHER":
                #a publisher just updates its internal value
                self.Driver.init(self.ParentConnectionParameters, self.channelPath)
            if self.mode == "SUBSCRIBER":
                #if a subscriber type, in order to get the value we subscribe to the publish path
                self.Driver.init(self.ParentConnectionParameters, self.ParentNodePath + self.name)
        else:
            raise Exception("Protocol "+args[4]+"not supported")

    def executeCMD(self, cmd, args):
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
    def init(self, args, path = ""):
        self.subscriberPath = path
        self.connArgs = json.loads(args)
        self.initDriver()
        self.value = ""
        self.lastSentCmd = ""
        self.lockUpdateFlag = False
        #self.initDriver()
        pass
    #locks the result until a new response is sent
    #since the backend is designed in this way this should
    #mitigate the effect of the delayed update
    def getLockFlag(self):
        return self.lockUpdateFlag

    def initDriver(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.connArgs["broker"], self.connArgs["port"], self.connArgs["keepalive"])

        taskListen = threading.Thread(target=self.clientlisten, args=(self.client,))
        taskListen.start()
        pass

    def clientlisten(self, arg):
        arg.loop_forever()
        pass

    def sendCommand(self,command, args):
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
        self.value = data["Value"]
        if self.lockUpdateFlag and self.lastSentCmd == self.value: #ToDo: a race condition may happens if no update received
            self.lockUpdateFlag = False
        pass