#application to integrate GSM sim900 firmware into mqtt broker

 #!/usr/bin/python
#coding:utf-8
import time
import threading
import json
import Serial

from nodeMqtt import nodeMqttHandler #ToDo: move to a global state

SEND_SMS_CMD = "SENDSMS"

SIM900SerialPort = None
#ToDo: Expect to retrive main configs such as:
# Broker host
'''
globalConfigs = {
	"name":"simDevice1",
	"mqttHost":'X.X.X.X',
	"mqttPort":1883
}
'''
def readGlobalConfigs():
	return jsonConfigs


#ToDo: Expect to read local configs such as:
# Expected serial port info
# Expected names for publisher
# Expected names for subscribers
'''
localConfigs = {
	"portPath":"COMXXX",
	"baudrate":9600,
	"localId":XXXXXXX
}
'''
def readLocalConfigs():
	return jsonLocalConfigs

def send_sms(message, args):
	try:
		msgObj = json.loads(message)
		args.write(SEND_SMS_CMD)
		args.write(0)
		time.sleep(0.01)
		args.write(msgObj["number"])
		args.write(0)
		time.sleep(0.01)
		args.write(msgObj["msg"])
		args.write(0)
	pass

if __name__ == "__main__":
	#ToDo: with the configs, use the nodeMqttHandler to define the endpoints/
	localConfigs = readLocalConfigs() #get local id
	configs = readGlobalConfigs() #get configs with local id
	
	SIM900SerialPort = serial.Serial(port=localConfigs["portPath"],baudrate=localConfigs["baudrate"])
	

	nodeProxy = nodeMqtt(configs["mqttHost"],configs["mqttPort"],configs["Name"])
	nodeProxy.connect()
	
	nodeProxy.add_subscriber(localConfigs["name"],"STRING",SIM900SerialPort)
	
	while True:
		nodeProxy.publish_manifest()
		time.sleep(7)
	pass