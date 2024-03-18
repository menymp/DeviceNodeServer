 #!/usr/bin/python
#coding:utf-8
import time
import threading
import paho.mqtt.client as mqtt
import json

class nodeDeviceDiscoveryTool():
    devicesFound = []
    def initNodeParameters(self, args, discoveryArgs):
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
            print("Protocol "+args[4]+" not supported")
        pass

    def stop(self):
        self.listener.stop()
    
    def getState(self):
        return self.state
    
    #{"Name":"Humidity","Mode":"PUBLISHER","Type":"FLOAT","Channel":"/MenyNode1/Humidity","Value":"40.00"}
    def addDiscoveredChildDevice(self,args):
        #print("Found device: " + args['Name'] + " " + args['Channel'])
        self.devicesFound.append(args)
        pass
    
    def discoveryListenerDone(self):
        #print("device discovery ended")
        self.state = "DONE"
        pass
        


class mqttNodeListener():
    def init(self, path, mqttBroketPath, callbackAddDevice, callbackDiscoveryDone, port = 1883, keepalive = 60):
        self.path = path #poner el manifest en el path NOTA IMPORTANTE
        self.mqttBroketPath = mqttBroketPath
        self.port = port
        self.keepalive = keepalive
        self.callbackAddDevice = callbackAddDevice
        self.callbackDiscoveryDone = callbackDiscoveryDone
        self.devicesAddedCount = 0
        pass
    
    def startMqttClient(self, mqttBrokerPath, on_connect, on_message, port, keepalive):
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
        client.subscribe(self.path + "manifest")
        

    def on_Manifestmessage(self, client, userdata, msg):
        try:
            self.Nodeclient.unsubscribe(self.path + "manifest")
            self.Nodeclient.disconnect()

            m_decode=str(msg.payload.decode("utf-8","ignore"))
            nodeManifest = json.loads(m_decode)
            
            self.nodeName = nodeManifest["Name"]
            self.RootName = nodeManifest["RootName"]
            self.Devices = nodeManifest["Devices"]
            
            
            
            self.clientDev, taskListen = self.startMqttClient(self.mqttBroketPath, self.on_Devconnect, self.listenDeviceChannel,self.port, self.keepalive)
            
            self.FoundDevices = []
            
            for devicePath in self.Devices:
                print("listen for device on:" + self.path + devicePath)
                self.clientDev.subscribe(self.path + devicePath)
            
        except:
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

            self.FoundDevices.append(deviceInfo["Name"])
            self.devicesAddedCount = self.devicesAddedCount + 1
            
            self.callbackAddDevice(deviceInfo)
            
            if self.allDevicesFound():
                self.clientDev.disconnect()
                self.callbackDiscoveryDone()
            
        except:
            #self.client.subscribe(self.path)
            pass 
        pass

    def allDevicesFound(self):
        flagfound = True
        for device in self.Devices:
            if not any(device in x for x in self.FoundDevices):
                flagfound = False
        return flagfound
        pass

    def deviceAlreadyFound(self, device):
        flagfound = False
        if any(device in x for x in self.FoundDevices):
            flagfound = True
        return flagfound
            
    
    
    