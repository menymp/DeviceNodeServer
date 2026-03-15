'''
Mar 2025

menymp

node_bridge.py

this class contains utilities for node unit utility protocol in python
its based on paho mqtt library

a redesign to change the communications dynamics from a server -> client discovery
to a client -> server reporting match
this class abstracts common patterns that originaly were scatered across all modules

'''
import time
import json
import paho.mqtt.client as mqtt
from network_utils_hal import network_utils_hal
from threading import Timer, Event


'''
message should have the following form
{
    "Name":"MenyGardenNode1",
    "RootName":"/MenyGardenNode1/",
    "ip": "x.x.x.x",
    "mac_addr": "xxxxxxxxx"
    "Devices": [
        {
            "Name":"PirSensor",
            "Mode":"PUBLISHER",
            "Type":"STRING",
            "Channel": "/MenyGardenNode1/PirSensor",
            "Value": "69.69"
        },
        {
            "Name":"WaterPump",
            "Mode":"SUBSCRIBER",
            "Type":"STRING",
            "Channel":""/MenyNode1/WatterSolenoid/state"",
            "Value": "ON"
        }
    ]

}
'''


'''

Build a decouple HAL to extract

IP ADDR
MAC

later abstract mqtt utils so it can be used in micropython and windows/linux
abstract threading as well if possible

'''

class node_bridge(network_utils_hal):
    timeout_ack = 6 # acknowledge timeout in secs
    register_topic_path = "/inbound" # main server topic path for data update and device changes registration
    broker_validation_path = "/node_name_request"
    # TODO: Port to MicroPython and C++

    
    def __init__(self, name, broker, port = 1883, keepalive = 60, sampling_time = 6, reconnect_time = 3):
        self.devices = []
        self.VALID_TYPES = [] # requested first with the ack
        self.mqtt_broker = broker
        self.mqtt_port = port
        self.mqtt_keepalive = keepalive
        self.sampling_time = sampling_time
        self.reconnect_time = reconnect_time
        self.Name = name
        self.RootPath = "/%s/" % name
        self.ip_addr = self.get_ip()
        self.mac_addr = self.get_mac()
        print("Got hw addr: %s %s" % (self.ip_addr, self.mac_addr))
        self.ack_event = Event()
        self.error_event = Event()
        self.timeout_event = Event()
        self.stop_event = Event()
        self.reconnect_event = Event()
        self.updt_event = Event()
        self.client = None
        self._backoff_time = self.reconnect_time
        pass

    def __init_mqtt_client__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        pass

    '''
    Disables mqtt background threads and resets ack flags
    '''
    def disable(self):
        print("stops client server")
        self.client.loop_stop()
        print("mqtt client stopped, clearing events")

        self.timeout_event.clear()
        self.error_event.clear()
        self.ack_event.clear()
        self.stop_event.set()
        self.client = None
        if self.tOut:
            self.tOut.cancel()
            self.tOut = None
        if self.t_payload:
            self.t_payload.cancel()
            self.t_payload = None
        pass
    
    '''
    handles abrupt disconnection, cases like:
    - lost mqtt broker connection
    - no heart beat received from server
    '''
    def _reconnect(self):
        if self.stop_event.is_set():
            print("Stop event set, aborting reconnect")
            return
        print("reconnection starting...")
        self.ack_event.clear()

        backoff = self._backoff_time
        while not self.stop_event.is_set() and not self._handle_init_acknowledge(True):
            print(f"Retrying register in {backoff} seconds...")
            for _ in range(backoff):
                if self.stop_event.is_set() or self.ack_event.is_set():
                    return
                time.sleep(1)
            self.ack_event.clear()
            self._register_node()
            backoff = min(backoff * 2, 60)
            self._backoff_time = backoff

    '''
    starts the acknowledge protocol with server
    '''
    def acknowledge(self):
        if self.client is None:
            self.__init_mqtt_client__()
        print("starting client mqtt")
        self.client.connect(self.mqtt_broker, self.mqtt_port, self.mqtt_keepalive)
        self.client.loop_start()
        self._handle_init_acknowledge()
        pass

    def _handle_init_acknowledge(self, retry=False):
        # Start timeout timer
        self._start_timeout()

        # Wait until one of the events is set
        while True:
            if self.stop_event.is_set():
                return True
            if self.timeout_event.is_set() and not retry:
                self.timeout_event.clear()
                raise RuntimeError("Took too long to acknowledge")
            elif self.timeout_event.is_set() and retry:
                self.timeout_event.clear()
                print("Timeout with retry")
                return False
            if self.error_event.is_set():
                raise RuntimeError(f"Acknowledge error, or name {self.Name} already in use")
            if self.ack_event.is_set():
                self.tOut.cancel()
                self._resubscribe_devices()
                print("Node successfully acknowledged, building payload")
                self._backoff_time = self.reconnect_time
                return True
            time.sleep(0.6)  # short sleep to avoid busy loop
        pass
    
    '''
    waits for server acknowledge response as a hearbeat
    '''
    def _handle_wait_update_acknowledge(self):
        if self.ack_event.is_set():
            return True   # <-- NEW
        # Start timeout timer
        self._start_timeout()

        # Wait until one of the events is set
        while True:
            if self.stop_event.is_set():
                break
            if self.timeout_event.is_set():
                print("Took too long to acknowledge, schedule attempt to reconnect")
                self.reconnect_event.set()
                return False
            if self.updt_event.is_set():
                self.tOut.cancel()
                self._resubscribe_devices()
                print("Node successfully acknowledged, exiting wait ack")
                return True
            time.sleep(0.6)  # short sleep to avoid busy loop
        pass
    
    '''
    builds payload string request with current callback values
    '''
    def _build_and_send_payload_manifest(self):
        if self.reconnect_event.is_set()  and not self.ack_event.is_set():
            print("Waiting for reconnection")
            self._reconnect()
            pass

        if self.stop_event.is_set():
            print("Payload skipped, server stopped")
            return
        
        if not self.ack_event.is_set():
            print("ERROR: No acknowledge finished")
            return

        manifest = {
            "Name": self.Name,
            "RootName": self.RootPath,
            "ip": self.ip_addr,
            "mac_addr": self.mac_addr,
            "acknowledge_path": self.ack_path,
            "Devices": []
        }
        for device in self.devices:
            device_snapshot = dict(device)
            device_snapshot["Value"] = device["value_callback"]() # reading current state
            # we dont need these callbacks for the snapshot output
            device_snapshot.pop("value_callback", None) # pop current value callback from snapshot 
            device_snapshot.pop("command_callback", None) # pop command callback from snapshot 
            manifest["Devices"].append(device_snapshot)
        manifest_payload = json.dumps(manifest)

        print(manifest_payload)
        try:
            self.client.publish(self.register_topic_path , manifest_payload)
        except Exception as e:
            print("Publish failed manifest:", e)
        
        self.updt_event.clear() # reset the ack update event

        self._handle_wait_update_acknowledge()
        # reschedule itself
        if self.t_payload:
            self.t_payload.cancel() #Clean previous timer
        self.t_payload = Timer(self.sampling_time, self._build_and_send_payload_manifest)
        self.t_payload.start()
        pass
    
    '''
    start server publish timer
    subscribes all defined device subscriptors
    '''
    def start_server(self):
        if not self.ack_event.is_set():
            print("ERROR: No acknowledge finished")
            return
        self.stop_event.clear()   # signal stop cleared
        self.t_payload = Timer(self.sampling_time, self._build_and_send_payload_manifest )
        self.t_payload.start()
        # now subscribe all subscriptors

        for device in self.devices:
            if device["Mode"] == "SUBSCRIBER":
                print("subscribed device path %s" % device["Channel"])
                self.client.subscribe(device["Channel"])
        pass

    '''
    stop server payload timer
    '''
    def stop_server(self):
        if not self.ack_event.is_set():
            print("ERROR: No acknowledge finished")
            return
        self.stop_event.set()   # signal stop
        if self.t_payload is None:
            print("Server is not started")
            return
        self.t_payload.cancel()
        self.t_payload = None

        for device in self.devices:
            if device["Mode"] == "SUBSCRIBER":
                print("unsubscribed device path %s" % device["Channel"])
                self.client.unsubscribe(device["Channel"])
        print("server payload stopped")
    
    '''
    starts ack timeout
    '''
    def _start_timeout(self):
        self.tOut = Timer(self.timeout_ack, self._timeout_error )
        self.tOut.start()
        pass
    
    '''
    timeout if ack was not completed in time
    '''
    def _timeout_error(self):
        self.timeout_event.set()
    
    '''
    Now device will attempt to confirm its name is not already in use
    '''
    def _on_connect(self, client, userdata, flags, rc):
        self._backoff_time = self.reconnect_time
        self._register_node()
        pass

    def _register_node(self):
        print("connection established, attempting to register node")
        self.ack_path = self.ip_addr + "/" + self.Name + "/ack"
        register_request = {
            "Name": self.Name,
            "AcknowledgePath": self.ack_path,
            "MacAddress": self.mac_addr
        }
        print("ack payload: %s" % register_request)
        self.client.subscribe(self.ack_path)
        register_request_payload = json.dumps(register_request)
        self.client.publish(self.broker_validation_path, register_request_payload)
        pass


    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print("Unexpected disconnection. rc =", rc)
            self.ack_event.clear()
            self.updt_event.clear()
            self.reconnect_event.set()
        else:
            print("Clean disconnect from broker")
    
    '''
    retrives a subscriber node callback
    '''
    def _get_subscriber_callback(self, topic):
        for device in self.devices:
            if device["Channel"] == topic and device["Mode"] == "SUBSCRIBER":
                return device
        return None
    
    '''
    handles commands received from server
    '''
    def _on_message(self, client, userdata, msg):
        self._backoff_time = self.reconnect_time   # <-- NEW
        messageValue=str(msg.payload.decode("utf-8","ignore"))
        print("registration response %s for %s" % (messageValue, msg.topic))

        if msg.topic == self.ack_path:
            serverResponse = json.loads(messageValue)
            result = serverResponse["result"]
            self.VALID_TYPES = serverResponse["valid_types"] # array
            if len(self.VALID_TYPES) == 0:
                self.error_event.set()
            elif result == "" or result == "ERR_ACK":
                self.error_event.set()
            elif result == "SUCCESS_ACK":
                self.ack_event.set()
                self.reconnect_event.clear()
                self.timeout_event.clear()
                self.updt_event.set()
            return
        else:
            target_device = self._get_subscriber_callback(msg.topic)
            if target_device is None:
                print("Device topic unknown %s" % msg.topic) #this should not happen at all, if so, something weird happened
                return
            print("Exec command: %s for device %s" % (messageValue, target_device["Name"]))
            target_device["command_callback"](messageValue)
        pass

    '''
    Indicates if device name already exists in the devices list
    '''
    def device_exists(self, name):
        if not self.ack_event.is_set():
            print("ERROR: No acknowledge finished")
            return False
        for device in self.devices:
            if device["Name"] == name:
                return True
            
        return False
    
    '''
    validates device init args
    name: name of the device
    type: data type of the device STRING NUMBER ...
    get_value_call: current value callback
    '''
    def _validate_device(self, name, type, get_value_call):
        if not self.ack_event.is_set():
            print("ERROR: No acknowledge finished")
            return
        if name == "" or name is None:
            raise ValueError("invalid name")
        if not type or type not in self.VALID_TYPES:
            raise ValueError("invalid type %s " % type)
        if get_value_call is None:
            raise ValueError("must provide a valid function")
        pass

    '''
    adds a new publisher to the mainfest, used for sensors to read data
    name: name of the device
    type: data type of the device STRING NUMBER ...
    get_value_call: current value callback
    '''
    def add_publisher_device(self, name, type, get_value_callback):
        if not self.ack_event.is_set():
            print("ERROR: No acknowledge finished")
            return
        if self.device_exists(name):
            raise RuntimeError("Device name %s already exists" % name)
        self._validate_device(name, type, get_value_callback)

        publisher = {
            "Name":name,
            "Mode":"PUBLISHER",
            "Type":type,
            "Channel": self.RootPath + name + "/value", #not in use considered new approach, leaved for legacy compatibility
            "value_callback": get_value_callback
        }
        self.devices.append(publisher)
        pass

    '''
    adds a new subscriber to the mainfest, used for actuators
    name: name of the device
    type: data type of the device STRING NUMBER ...
    get_value_call: current value callback
    command_callback: callback to call when a command was received for its topic
    '''
    def add_subscriber_device(self, name, type, get_value_callback, command_callback):
        if not self.ack_event.is_set():
            print("ERROR: No acknowledge finished")
            return
        if self.device_exists(name):
            raise RuntimeError("Device name %s already exists" % name)
        self._validate_device(name, type, get_value_callback)
        channel_path = self.RootPath + name + "/value"

        subscriber = {
            "Name":name,
            "Mode":"SUBSCRIBER",
            "Type":type,
            "Channel": channel_path,
            "value_callback": get_value_callback,
            "command_callback": command_callback
        }
        self.client.subscribe(channel_path)
        self.devices.append(subscriber)
        pass
    
    '''
    under a disconnection event resubscribes all subscriber devices
    '''
    def _resubscribe_devices(self):
        for device in self.devices:
            if device["Mode"] == "SUBSCRIBER":
                self.client.subscribe(device["Channel"])
        pass

    '''
    removes a device from the main list
    name: name of the device
    '''
    def remove_device(self, name):
        print("removing device %s" % name)
        for device in self.devices:
            if name == device["Name"]:
                print("removed device %s" % name)
                self.devices.remove(device)
                break
        pass
