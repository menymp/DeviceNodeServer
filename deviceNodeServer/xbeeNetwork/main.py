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
    def __init__(self, discoveryTime = 20):
        self.networkDevices = []
        self.discoveryTime = discoveryTime
        self.stopSearch = True
        pass

    def init(self, port_path, baud_rate, message_received_callback = None, sync_devices_callback = None):
        self.coordinatorDevice = XBeeDevice(port_path, baud_rate)
        self.coordinatorDevice.open()
        self.coordinatorDevice.add_data_received_callback(self._message_arrived_callback)
        self._message_received_callback = message_received_callback
        self._sync_devices_callback = sync_devices_callback
        self._initXbeeNetwork()
        pass
    
    def start(self):
        self.searchTimer = Timer(self.discoveryTime, self._discoveryDevices).start()
        self.stopSearch = False
        pass

    def stop(self):
        self.stopSearch = True
        pass

    def close(self):
        self.stop()
        self.coordinatorDevice.close()
        pass

    def sendMessage(self, address64bit, data):
        exists, remoteDevice = self.deviceExists(address64bit)
        if not exists:
            return False
        self.coordinatorDevice.send_data(remoteDevice, data)
            
        pass

    def deviceExists(self, address64bit):
        device = None
        found = False
        for xbeeDevice in self.networkDevices:
            if xbeeDevice.get_64bit_addr() == address64bit:
                device = xbeeDevice
                found = True
                break
        return found, device
    
    def _message_arrived_callback(self, xbee_message):
        if self._message_received_callback is None:
             print("Warning! message received without callback!")
             return
        address = xbee_message.remote_device.get_64bit_addr()
        data = xbee_message.data.decode("utf8")
        self._message_received_callback(address, data)
        pass
    
    def _initXbeeNetwork(self):
        self.xbee_network = self.coordinatorDevice.get_network()
        self.xbee_network.set_discovery_timeout(self.discoveryTime)
        self.xbee_network.clear()
        # Callback for discovered devices.
        def callback_device_discovered(remote):
            print("Device discovered: %s" % remote)
        # Callback for discovery finished.
        def callback_discovery_finished(status):
            if status == NetworkDiscoveryStatus.SUCCESS:
                print("Discovery process finished successfully.")
            else:
                print("There was an error discovering devices: %s" % status.description)
        
        self.xbee_network.add_device_discovered_callback(callback_device_discovered)
        self.xbee_network.add_discovery_process_finished_callback(callback_discovery_finished)
        pass
    
    #This Task is performed often to discover available devices
    def _discoveryDevices(self):
        print("scanning Xbee network for available devices")
        #device = XBeeDevice(PORT, BAUD_RATE)
        try:
            self.xbee_network.start_discovery_process()
            print("Discovering remote XBee devices...")
            while self.xbee_network.is_discovery_running():
                time.sleep(0.1)
        finally:
            if self.coordinatorDevice is not None and self.coordinatorDevice.is_open():
                self.coordinatorDevice.close()
        self.networkDevices = self.xbee_network.get_devices()
        self._sync_devices_callback(self.networkDevices)
        self.searchTimer = Timer(self.discoveryTime, self._discoveryDevices).start() if not self.stopSearch else None

	
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
def message_received_callback(address64bit, data):
	print("Received data from %s: %s" % (address64bit, data))
	
	#ToDo: add device callback
	#	   Create as a class
	pass
	
def sync_devices_mqtt(devices, nodeProxy):
    for xbeeDevice in devices:
        #ToDo: map this to nodeProxy with the id
        if not nodeProxy.deviceExists(name=#######):
            nodeProxy.add_publisher(........)
            nodeProxy.add_subscriber(......)
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