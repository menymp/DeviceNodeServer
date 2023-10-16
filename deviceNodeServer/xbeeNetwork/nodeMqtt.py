import time
import threading
import paho.mqtt.client as mqtt
import json


mqx_tmp =  {
    "Name":Name,
    "Mode":"PUBLISHER",
    "Type":"STRING",
    "Channel":Channel,
    "Value":str(value)
}

class nodeMqttHandler():
	def __init__(self, brokerHost, brokerPort, nodeName, keepalive = 60):
		self.brokerHost = brokerHost
		self.brokerPort = brokerPort
		self.keepalive = keepalive
		
		self.devices = []
		
		self.name = nodeName
		self.rootpath = '/' + nodeName + '/'
		pass
	
	def connect(self):
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.connect(self.brokerHost, self.brokerPort, self.keepalive)
		
		self.taskListen = threading.Thread(target=self._task_clientLoop)
        self.taskListen.start()
		return True
	
	#stops the mqtt main task
	def disconnect(self):
		self.client.disconnect()
	
	def add_subscriber(self, Name, dataType, callback, valueName = 'value', args = None):
		mqx_tmp =  {
			"Name":Name,
			"Mode":"SUBSCRIBER",
			"Type":dataType,
			"Channel":self.path + Name + '/' + valueName,
			"Value":None
		}
		self.devices.add((mqx_tmp, callback, args))
		self.client.subscribe(mqx_tmp["Channel"])
		return True
	
	def add_publisher(self, Name, dataType, path):
		devExists, devObj = self.deviceExists(name=Name)
		if devExists:
			raise ValueError('Device name already exists!')
		mqx_tmp =  {
			"Name":Name,
			"Mode":"PUBLISHER",
			"Type":dataType,
			"Channel":self.path + Name,
			"Value":None
		}
		self.devices.add((mqx_tmp,None))
		return True
	
	def publishValue(self, Name, value);
		devExists, device = self.deviceExists(name=Name)
		if not devExists:
			raise ValueError('Device name does NOT exists!')
		if device[0]["Mode"] == "SUBSCRIBER":
			raise ValueError('Device Mode does not support publish!')
		#ToDo: a value check should be performed
		device[0]["Value"] = value
		self.client.publish(device[0]["Channel"],str(value))
		
		
	
	def deviceExists(self, name = None, channel = None):
		deviceExists = False
		deviceObj = None
		if(name is None and topic is None):
			raise ValueError('Provide at least a channel name or a topic')
		#check if device exists
		for device in self.devices:
			if(name is not None and device[0].Name == Name or 
			channel is not None and device[0].Channel == channel):
				deviceExists = True
				deviceObj = device
				break
		return deviceExists, deviceObj
	
	def _on_connect(self):
		pass
	
	def _on_message(self, client, userdata, msg):
        try:
			topic=str(msg.topic.decode("utf-8","ignore"))
            m_decode=str(msg.payload.decode("utf-8","ignore"))
			
			devExists, device = self.deviceExists(channel=topic)
			#check if callback is known
			if not devExists:
				return
			if len(device) != 3 or device[0]["Mode"] != "SUBSCRIBER" or device[1] is None:
				return
			#once validated everithing is correct, do the callback
			device[1](m_decode, device[2])
            device[0]["Value"] = m_decode
        except:
            #self.client.subscribe(self.path)
            pass 
        pass
	
	def publish_manifest(self):
		#Publish the existing devices manifest
		deviceList = []
		for device in self.devices:
			deviceList.append(device[0]["Name"])
			self.client.publish(self.rootpath + device[0]["Name"], json.dumps(device[0])
		
		manifest = {
			"Name":self.name,
			"RootName":self.rootpath,
			"Devices":deviceList
		}
		self.client.publish(self.rootpath + 'manifest',json.dumps(manifest))	
		pass
	
	def _task_clientLoop(self):
		self.client.loop_forever()