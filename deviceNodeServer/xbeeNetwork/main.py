'''
Network adapter for device manager system and xbee shield
menymp

this app works as a sub register that allow receiving and transfer of
data from and to xbee network.

The application starts with a discovery of each device and creates a list of devices.
this is performed periodicaly and allow to incorporate new devices into the network.

with the existing devices, a manifest is then created in the same way as other mqtt devices

then each device information is forward relayed to a subtopic for publisher and subscribers
in the case of subscribers, an aditional subscription is created in order to accept incomming commands.


In construction ...
'''

import time
import threading
from threading import Timer
import json
import sys

sys.path.append('../Libraries')
from NodeMqttClient import NodeMqttClient
from XbeeNetMqttCoordinator import XbeeNetMqttCoordinator
import signal


# TODO: Replace with the serial port where your local module is connected to.
PORT = "COM1"
# TODO: Replace with the baud rate of your local module.
BAUD_RATE = 9600

def readConfigFile( path = './configs.json'):
	with open(path) as f:
		data = json.load(f)
	return data

class XbeeNetworkController():
    def __init__(self, configs):
        self.nodeProxy = NodeMqttClient(configs["mqtt-host"],configs["mqtt-port"],configs["name"])
        self.xbeeCoordinator = XbeeNetMqttCoordinator()
        self.configs = configs
        pass

    def start(self):
        self.xbeeCoordinator.init(self.configs["comm-port-path"], self.configs["com-baud-rate"], self._message_received_callback, self._sync_devices_mqtt)
        self.nodeProxy.connect()
        self.xbeeCoordinator.start()
        pass

    def stop(self):
        self.nodeProxy.disconnect()
        self.xbeeCoordinator.stop()
        self.xbeeCoordinator.close()
        pass
    
    #From Xbee to mqtt network
    def _message_received_callback(self, address64bit, data):
        print("Received data from %s: %s" % (address64bit, data))
        self.nodeProxy.publishValue(str(address64bit) + "_OUT", data)
        pass
    
    #From mqtt network to Xbee, args in this case is the 64 bit addr
    def _callbackReceivedMessage(self, message, args):
        try:
            self.xbeeCoordinator.sendMessage(args, message)
        except:
            print("error processing: " + str(message) + " args: " + str(args))
        pass

    def _sync_devices_mqtt(self, devices):
        for xbeeDevice in devices:
            #ToDo: map this to nodeProxy with the id
            publishExists, _ = self.nodeProxy.deviceExists(name=(xbeeDevice + "_OUT"))
            subscribeExists, _ = self.nodeProxy.deviceExists(name=(xbeeDevice + "_IN"))
            if not publishExists:
                print("add publish")
                self.nodeProxy.add_publisher(xbeeDevice + "_OUT","STRING")
            if not subscribeExists:
                print("add subscribe")
                self.nodeProxy.add_subscriber(xbeeDevice + "_IN",self._callbackReceivedMessage, xbeeDevice.get_64bit_addr())
        pass

    def publish_manifest(self):
        self.nodeProxy.publish_manifest()
        pass

	
'''
# Instantiate a local XBee node.
xbee = XBeeDevice("COM1", 9600)
xbee.open()

# Define the callback.
def my_data_received_callback(xbee_message):
    address = xbee_message.remote_device.get_64bit_addr()
    data = xbee_message.data.decode("utf8")
    print("Received data from %s: %s" % (address, data))

# Add the callback.
xbee.add_data_received_callback(my_data_received_callback)
'''
#when message is received from 

#ToDo: add mqtt manifest callback for compliance with devices
#each device will create a channel under mqtt standard broker


if __name__ == '__main__':
    configs = readConfigFile()

    xbeeServer = XbeeNetworkController(configs)
    xbeeServer.start()

    def signal_term_handler(signal, frame):
        xbeeServer.stop()
        print('exit process')
        sys.exit(0)
    signal.signal(signal.SIGTERM, signal_term_handler)

    while True:
        xbeeServer.publish_manifest()
        time.sleep(configs["manifest-publish-delay"])
    pass