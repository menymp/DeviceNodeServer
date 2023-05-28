from dbActions import dbDevicesActions
import threading
import json
import time
import threading
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

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

    def executeCMDJson(self, jsonArgs):
        objCmd = json.loads(jsonArgs)
        #strVal = objCmd['idDevice']
        #strVal2 = objCmd['command']
        #strVal3 = objCmd['args']
        return self.executeCMD(objCmd['idDevice'], objCmd['command'], objCmd['args'])

    def executeCMD(self, idDevice, command, args):
        result = ""
        for device in self.Devices:
            if device.id == idDevice:
                result = device.executeCMD(command,args)
                break
        dictionary = {'result':result}
        jsonString = json.dumps(dictionary, indent=4)
        return jsonString 
		
		#toDo: still in proof of concept expect for a better approach
	def execCommand(inputArgs):
		#parses the command
		#list devices
		
		inTks = inputArgs
		
		if inTks[0] == 'ls':
			return str(self.Devices)
		elif inTks[0] == "run":
			result = self.executeCMD(inTks[1],inTks[2],inTks[3])
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
                self.Driver.init(self.ParentConnectionParameters, self.channelPath)
            if self.mode == "SUBSCRIBER":
                self.Driver.init(self.ParentConnectionParameters)
        else:
            raise Exception("Protocol "+args[4]+"not supported")

    def executeCMD(self, cmd, args):
        result = ""
        if self.mode == 'PUBLISHER':
            result = self.Driver.getValue()
            self.value = result
        if self.mode == 'SUBSCRIBER':
            self.Driver.sendCommand(cmd, self.channelPath)
            result = "OK"
        return result

class mqttDriver():
    def init(self, args, path = ""):
        self.subscriberPath = path
        self.connArgs = json.loads(args)
        self.initDriver()
        self.value = ""
        #self.initDriver()
        pass

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
        pass