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
	def __init__(self, brokerHost, nodeName, path):
		pass
	
	def connect(self):
		#ToDo: attempts to connect to mqtt system
		return True
	
	def add_subscriber(self, topic, Name, dataType, callback):
		#ToDo: init subscriber and add a callback, add to the manifest
		return True
	
	def add_publisher(self, topic, Name, dataType):
		return True
	
	def publishValue(self, Name, value);
		#publish a value if the publisher was initialized device exists
		pass
		
	def _addManifestEntry(self, manifestEntry):
		return True
	
	def _publishManifest(self):
		#Publish the existing devices manifest
		pass