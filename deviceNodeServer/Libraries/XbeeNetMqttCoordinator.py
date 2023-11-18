import time
from threading import Timer, Thread, Event
import queue
from digi.xbee.models.status import NetworkDiscoveryStatus
from digi.xbee.devices import XBeeDevice, RemoteXBeeDevice
from digi.xbee.models.address import XBee64BitAddress

class XbeeNetMqttCoordinator():
    def __init__(self, discoveryTime = 20, max_request_size=10):
        self.networkDevices = []
        self.remoteDevices = []
        self.remoteStrAddresses = []
        self.discoveryTime = discoveryTime
        self.stopSearch = True
        self.stop_event = Event()
        self.search_devices = Event()
        self.incoming_requests = queue.Queue(maxsize=10)
        self.state_index = 0
        pass
    
    #Process incomming messages from network as a queue
    def _task_submit_messages(self):
        while not self.stop_event.is_set():
            if self.search_devices.is_set():
                self._discoveryDevices(self)
                self.search_devices.reset()
            
            if not self.incoming_requests.empty():
                net_msg = self.incoming_requests.pop()
                if not self.sendMessage(net_msg["address"],net_msg["data"]):
                    print("Error, full QUEUE")
            self._update_state()
            pass
    
    def _update_state(self):
        remoteDevice = self.remoteDevices[self.state_index]
        self.coordinatorDevice.send_data(remoteDevice, "UPDATE") #Every device should respond with a current value state and send to out
        
        self.state_index = self.state_index + 1
        if self.state_index == (self.remoteDevices.len() - 1):
            self.state_index = 0
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
        self.searchTimer = Timer(self.discoveryTime, self._set_search_flag).start()
        self.stopSearch = False
        self.stop_event.reset()
        self.search_devices.set()
        self.state_index = 0
        self._task_handle_requests = Thread(target=self._task_submit_messages)
        self._task_handle_requests.start()
        pass

    def stop(self):
        self.stopSearch = True
        self.search_devices.reset()
        self.stop_event.reset()
        self.state_index = 0
        pass

    def close(self):
        self.stop()
        self.coordinatorDevice.close()
        pass
    
    def _sendCoordinatorMessage(self, address64String, data):
        exists, remoteDevice = self.deviceExists(address64String)
        if not exists:
            return False
        self.coordinatorDevice.send_data(remoteDevice, data)
        pass

    def sendMessage(self, address64String, data):
        msg = {
            "address":address64String,
            "data":data
        }
        if not self.incoming_requests.full():
            self.incoming_requests.put(msg)
            return True
        return False

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

    def _set_search_flag(self):
        self.search_devices.set()
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
            exists, _ = self.deviceExists(str(device.get_64bit_addr()))
            if exists:
                continue
            self.remoteDevices.append(RemoteXBeeDevice(self.coordinatorDevice, device.get_64bit_addr()))
            self.remoteStrAddresses.append(str(device.get_64bit_addr()))
        print("Available network devices" + str(self.remoteStrAddresses))
        self._sync_devices_callback(self.remoteStrAddresses)
        self.searchTimer = Timer(self.discoveryTime, self._discoveryDevices).start() if not self.stopSearch else None