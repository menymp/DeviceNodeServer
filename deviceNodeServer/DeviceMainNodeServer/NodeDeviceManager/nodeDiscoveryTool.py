 #!/usr/bin/python
#coding:utf-8
import time
import threading
import paho.mqtt.client as mqtt
import json
import sys
from os.path import dirname, realpath, sep, pardir

sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")
from loggerUtils import get_logger
logger = get_logger(__name__)

class nodeDeviceDiscoveryTool():
    devicesFound = []
    def initNodeParameters(self, args, discoveryArgs):
        logger.info("node discovery tool started with %s" % (args, discoveryArgs))
        #[id,nodename,path,parameters,protocolname]
        #[arguments for the search protocol]
        self.discoveryArgs = discoveryArgs

        self.idNode = args[0]
        self.nodename = args[1]
        self.path = args[2]
        self.parameters = args[3]
        self.protocolname = args[4]
        self.state = "WAIT"
        self.devicesFound = []
        
        if(args[4] == "MQTT"):
            #[broker server address]
            self.listener = mqttNodeListener()
            self.listener.init(self.path, self.discoveryArgs, self.addDiscoveredChildDevice, self.discoveryListenerDone)
            self.listener.start()
        else:
            #raise Exception("Protocol "+args[4]+"not supported")
            logger.error("Protocol "+args[4]+" not supported")
        pass

    def stop(self):
        logger.info("node discovery stopped")
        self.listener.stop()
    
    def getState(self):
        return self.state
    
    #{"Name":"Humidity","Mode":"PUBLISHER","Type":"FLOAT","Channel":"/MenyNode1/Humidity","Value":"40.00"}
    def addDiscoveredChildDevice(self,args):
        logger.info("new child discovered %s" % args)
        #print("Found device: " + args['Name'] + " " + args['Channel'])
        self.devicesFound.append(args)
        pass
    
    def discoveryListenerDone(self):
        logger.info("discovery finished")
        #print("device discovery ended")
        self.state = "DONE"
        pass
        


class mqttNodeListener():
    def init(self, path, mqttBroketPath, callbackAddDevice, callbackDiscoveryDone, port = 1883, keepalive = 60):
        logger.info("mqtt node listener started with %s" % (path, mqttBroketPath, callbackAddDevice, callbackDiscoveryDone, port, keepalive))
        self.path = path #poner el manifest en el path NOTA IMPORTANTE
        self.mqttBroketPath = mqttBroketPath
        self.port = port
        self.keepalive = keepalive
        self.callbackAddDevice = callbackAddDevice
        self.callbackDiscoveryDone = callbackDiscoveryDone
        self.devicesAddedCount = 0
        pass
    
    def startMqttClient(self, mqttBrokerPath, on_connect, on_message, port, keepalive):
        logger.info("starting client mqtt")
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(mqttBrokerPath, port, keepalive)
        
        taskListen = threading.Thread(target=self.clientlisten, args=(client,)) #ToDo: instead of thread, think to use the loop() function and do a pool, also handle the reconnect
        taskListen.start()
        return client, taskListen

    def clientlisten(self, arg):
        arg.loop_forever()
        pass
    
    def start(self):
        self.Nodeclient, taskListen = self.startMqttClient(self.mqttBroketPath, self.on_Manifestconnect, self.on_Manifestmessage,self.port, self.keepalive)  

    def stop(self):
        self.Nodeclient.disconnect() # disconnect gracefully
        self.Nodeclient.loop_stop() # stops network loop
    
    def on_Manifestconnect(self, client, userdata, flags, rc):
        logger.info("manifest linked %s" % (client))
        client.subscribe(self.path + "manifest")
        

    def on_Manifestmessage(self, client, userdata, msg):
        try:
            self.Nodeclient.unsubscribe(self.path + "manifest")
            self.Nodeclient.disconnect()
            
            m_decode=str(msg.payload.decode("utf-8","ignore"))
            logger.info("manifest discovered %s" % (m_decode))
            nodeManifest = json.loads(m_decode)
            
            self.nodeName = nodeManifest["Name"]
            self.RootName = nodeManifest["RootName"]
            self.Devices = nodeManifest["Devices"]
            
            
            
            self.clientDev, taskListen = self.startMqttClient(self.mqttBroketPath, self.on_Devconnect, self.listenDeviceChannel,self.port, self.keepalive)
            
            self.FoundDevices = []
            
            for devicePath in self.Devices:
                logger.info("listen for device on:" + self.path + devicePath)
                self.clientDev.subscribe(self.path + devicePath)
            
        except:
            logger.error("an error ocurred processing manifest")
            self.client.subscribe(self.path)
            pass
    
    
    def on_Devconnect(self, client, userdata, flags, rc):
        pass
    
    def listenDeviceChannel(self, client, userdata, msg):
        try:
            m_decode=str(msg.payload.decode("utf-8","ignore"))
            deviceInfo = json.loads(m_decode)
            
            if self.deviceAlreadyFound(deviceInfo["Name"]):
                return
            
            logger.info("new device info added %s" % deviceInfo)
            self.FoundDevices.append(deviceInfo["Name"])
            self.devicesAddedCount = self.devicesAddedCount + 1
            
            self.callbackAddDevice(deviceInfo)
            
            if self.allDevicesFound():
                logger.info("all devices found")
                self.clientDev.disconnect()
                self.callbackDiscoveryDone()
            
        except:
            #self.client.subscribe(self.path)
            logger.info("an error ocurred listening to device channel")
            pass 
        pass

    def allDevicesFound(self):
        flagfound = True
        for device in self.Devices:
            if not any(device in x for x in self.FoundDevices):
                flagfound = False
        return flagfound

    def deviceAlreadyFound(self, device):
        flagfound = False
        if any(device in x for x in self.FoundDevices):
            flagfound = True
        return flagfound
            
    
    
    