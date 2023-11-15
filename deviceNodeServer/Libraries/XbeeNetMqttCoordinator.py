import time
from threading import Timer
from digi.xbee.models.status import NetworkDiscoveryStatus
from digi.xbee.devices import XBeeDevice, RemoteXBeeDevice
from digi.xbee.models.address import XBee64BitAddress

class XbeeNetMqttCoordinator():
    def __init__(self, discoveryTime = 20):
        self.networkDevices = []
        self.remoteDevices = []
        self.remoteStrAddresses = []
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

    def sendMessage(self, address64String, data):
        exists, remoteDevice = self.deviceExists(address64String)
        if not exists:
            return False
        self.coordinatorDevice.send_data(remoteDevice, data)
        pass

    def deviceExists(self, address64String):
        device = None
        found = False
        for xbeeDevice in self.remoteDevices:
            if str(xbeeDevice.get_64bit_addr()) == address64String:
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
            pass
            #if self.coordinatorDevice is not None and self.coordinatorDevice.is_open():
            #    self.coordinatorDevice.close()
        self.networkDevices = self.xbee_network.get_devices()
        for device in self.networkDevices:
            self.remoteDevices.append(RemoteXBeeDevice(self.coordinatorDevice, device.get_64bit_addr()))
            self.remoteStrAddresses.append(str(device.get_64bit_addr()))
        print("devices for sync !!!!!!!!!!!!!!!!!")
        print(self.remoteStrAddresses)
        self._sync_devices_callback(self.remoteStrAddresses)
        self.searchTimer = Timer(self.discoveryTime, self._discoveryDevices).start() if not self.stopSearch else None