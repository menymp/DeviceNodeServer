#application to integrate GSM sim900 firmware into mqtt broker

 #!/usr/bin/python
#coding:utf-8
import time
import threading
import json
import Serial
import sys
import signal

sys.path.append('../Libraries')
from NodeMqttClient import NodeMqttClient

SEND_SMS_CMD = "SENDSMS"

SIM900SerialPort = None
'''
globalConfigs = {
	"name":"simDevice1",
	"mqttHost":'X.X.X.X',
	"mqttPort":1883
}
'''
def readGlobalConfigs():
	return jsonConfigs


'''
localConfigs = {
	"portPath":"COMXXX",
	"baudrate":9600,
	"localId":XXXXXXX
}
'''
def readConfigFile(self, path = './configs.json'):
	with open(path) as f:
		data = json.load(f)
	return data

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
	except:

	pass

if __name__ == "__main__":
	configs = readConfigFile() #get local info
	
	SIM900SerialPort = Serial.Serial(port=configs["gsm-serial-port-path"],baudrate=configs["gsm-serial-baudrate"])
	

	nodeProxy = NodeMqttClient(configs["mqtt-host"],configs["mqtt-port"],configs["name"])
	nodeProxy.connect()
	
	def signal_term_handler(signal, frame):
		nodeProxy.stop()
		print('exit process')
		sys.exit(0)
	signal.signal(signal.SIGTERM, signal_term_handler)

	nodeProxy.add_subscriber("send","STRING",send_sms, "message", SIM900SerialPort)
	nodeProxy.add_publisher("state", "STRING")

	#nodeProxy.publishMessage("state","example state!!!")
	
	while True:
		nodeProxy.publish_manifest()
		time.sleep(configs["manifest-publish-delay"])
	pass