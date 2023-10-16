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
import json
from digi.xbee.models.status import NetworkDiscoveryStatus
from digi.xbee.devices import XBeeDevice
from nodeMqtt import nodeMqttHandler


# TODO: Replace with the serial port where your local module is connected to.
PORT = "COM1"
# TODO: Replace with the baud rate of your local module.
BAUD_RATE = 9600

def get_global_configs():
	return globalConfigs

def get_local_configs():
	return localConfigs

class xbeeNetMqttCoordinator():
	def __init__(self):
		pass
	#... put relevant stuff there
	pass

#This Task is performed often to discover available devices
def discoveryDevices(device):
    print("scanning Xbee network for available devices")

    #device = XBeeDevice(PORT, BAUD_RATE)

    try:
        device.open()
        xbee_network = device.get_network()
        xbee_network.set_discovery_timeout(15)  # 15 seconds.
        xbee_network.clear()

        # Callback for discovered devices.
        def callback_device_discovered(remote):
            print("Device discovered: %s" % remote)

        # Callback for discovery finished.
        def callback_discovery_finished(status):
            if status == NetworkDiscoveryStatus.SUCCESS:
                print("Discovery process finished successfully.")
            else:
                print("There was an error discovering devices: %s" % status.description)

        xbee_network.add_device_discovered_callback(callback_device_discovered)

        xbee_network.add_discovery_process_finished_callback(callback_discovery_finished)

        xbee_network.start_discovery_process()

        print("Discovering remote XBee devices...")

        while xbee_network.is_discovery_running():
            time.sleep(0.1)

    finally:
        if device is not None and device.is_open():
            device.close()
	return xbee_network.get_devices()


def sync_devices_mqtt(devices, nodeProxy):
	for xbeeDevice in devices:
		#ToDo: map this to nodeProxy with the id
		if not nodeProxy.deviceExists(name=#######):
			nodeProxy.add_publisher(........)
			nodeProxy.add_subscriber(......)
	pass

def initXbeeCoordinator(port_path, baud_rate, message_received_callback):
	xbee = XBeeDevice("COM1", 9600)
	xbee.open()
	
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
def message_received_callback(xbee_message):
	address = xbee_message.remote_device.get_64bit_addr()
	data = xbee_message.data.decode("utf8")
	print("Received data from %s: %s" % (address, data))
	
	#ToDo: add device callback
	#	   Create as a class
	pass
	

#ToDo: add mqtt manifest callback for compliance with devices
#each device will create a channel under mqtt standard broker
if __name__ == '__main__':
	localConfigs = get_local_configs()
	configs = get_global_configs()
	
	nodeProxy = nodeMqtt(configs["mqttHost"],configs["mqttPort"],configs["Name"])
	nodeProxy.connect()
	
	
	
	while True:
		nodeProxy.publish_manifest()
		time.sleep(7)
    pass