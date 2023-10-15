#application to integrate GSM sim900 firmware into mqtt broker

 #!/usr/bin/python
#coding:utf-8
import time
import threading
import paho.mqtt.client as mqtt
import json

from nodeMqtt import nodeMqttHandler

#ToDo: Expect to retrive main configs such as:
# Broker host
def readGlobalConfigs():
	return jsonConfigs

#ToDo: Expect to read local configs such as:
# Expected serial port info
# Expected names for publisher
# Expected names for subscribers
def readLocalConfigs():
	return jsonLocalConfigs


if __name__ == "__main__":
	#ToDo: with the configs, use the nodeMqttHandler to define the endpoints/

	pass