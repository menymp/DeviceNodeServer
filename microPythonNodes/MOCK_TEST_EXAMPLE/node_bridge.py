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
import network_utils_hal
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
    VALID_TYPES = ["STRING", "NUMBER"]

    
    def __init__(self, name, broker, port = 1883, keepalive = 60, sampling_time = 6):
        self.devices = []
        self.mqtt_broker = broker
        self.mqtt_port = port
        self.mqtt_keepalive = keepalive
        self.sampling_time = sampling_time
        self.Name = name
        self.RootPath = "/%s/" % name
        self.ip_addr = self.get_ip()
        self.mac_addr = self.get_mac()
        print("Got hw addr: %s %s" % (self.ip_addr, self.mac_addr))
        self.ack_event = Event()
        self.error_event = Event()
        self.timeout_event = Event()
        self.stop_event = Event()
        pass

    '''
    starts the acknowledge protocol with server
    '''
    def acknowledge(self):
        print("starting client mqtt")
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.connect(self.mqtt_broker, self.mqtt_port, self.mqtt_keepalive)
        self.client.loop_start()

        # Start timeout timer
        self._start_timeout()

        # Wait until one of the events is set
        while True:
            if self.timeout_event.is_set():
                raise RuntimeError("Took too long to acknowledge")
            if self.error_event.is_set():
                raise RuntimeError(f"Acknowledge error, or name {self.Name} already in use")
            if self.ack_event.is_set():
                self.tOut.cancel()
                self.client.unsubscribe(self.ack_path)
                print("Node successfully acknowledged, building payload")
                break
            time.sleep(0.6)  # short sleep to avoid busy loop
        pass
    
    '''
    builds payload string request with current callback values
    '''
    def _build_and_send_payload_manifest(self):
        if self.stop_event.is_set():
            print("Payload skipped, server stopped")
            return
        
        if not self.ack_event.is_set():
            raise RuntimeError("No acknowledge finished")
        manifest = {
            "Name": self.Name,
            "RootName": self.RootPath,
            "ip": self.ip_addr,
            "mac_addr": self.mac_addr,
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

        self.client.publish(self.register_topic_path , manifest_payload)

        # reschedule itself
        self.t_payload = Timer(self.sampling_time, self._build_and_send_payload_manifest)
        self.t_payload.start()
        pass
    
    '''
    start server publish timer
    subscribes all defined device subscriptors
    '''
    def start_server(self):
        if not self.ack_event.is_set():
            raise RuntimeError("No acknowledge finished")
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
            raise RuntimeError("No acknowledge finished")
        self.stop_event.set()   # signal stop
        if self.t_payload is None:
            print("Server is not started")
            return
        self.t_payload.cancel()

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
    TODO: in the future rely on MAC instead
    '''
    def _on_connect(self):
        print("connection established, attempting to register node")
        self.ack_path = self.ip_addr + "/ack"
        register_request = {
            "Name": self.Name,
            "AcknowledgePath": self.ack_path
        }
        print("ack payload: %s" % register_request)
        self.client.subscribe(self.ack_path)
        register_request_payload = json.dumps(register_request)
        self.client.publish(self.broker_validation_path, register_request_payload)
        pass
    
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
        messageValue=str(msg.payload.decode("utf-8","ignore"))
        print("registration response %s for %s" % (messageValue, msg.topic))

        if msg.topic == self.ack_path:
            if messageValue == "" or messageValue == "ERR_ACK":
                self.error_event.set()
            elif messageValue == "SUCCESS_ACK":
                self.ack_event.set()
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
            raise RuntimeError("No acknowledge finished")
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
            raise RuntimeError("No acknowledge finished")
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
            raise RuntimeError("No acknowledge finished")
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
            raise RuntimeError("No acknowledge finished")
        if self.device_exists(name):
            raise RuntimeError("Device name %s already exists" % name)
        self._validate_device(name, type, get_value_callback)

        subscriber = {
            "Name":name,
            "Mode":"SUBSCRIBER",
            "Type":type,
            "Channel": self.RootPath + name + "/value",
            "value_callback": get_value_callback,
            "command_callback": command_callback
        }
        self.devices.append(subscriber)
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