import time
import ujson as json
from umqtt.simple import MQTTClient
import network
import ubinascii
import urandom
import gc

class network_utils_hal:
    def get_ip(self, wait=True, timeout=15):
        sta_if = network.WLAN(network.STA_IF)
        start = time.time()
        while wait and not sta_if.isconnected():
            if time.time() - start > timeout:
                raise RuntimeError("WiFi not connected after timeout")
            time.sleep(1)
        if not sta_if.isconnected():
            raise RuntimeError("WiFi not connected")
        return sta_if.ifconfig()[0]

    def get_mac(self):
        mac_bytes = network.WLAN().config('mac')
        return ':'.join('{:02x}'.format(b) for b in mac_bytes)

class node_bridge(network_utils_hal):
    def __init__(self, name, broker, port=1883, keepalive=60, sampling_time=6):
        # Public configuration
        self.Name = name
        self.mqtt_broker = broker
        self.mqtt_port = port
        self.mqtt_keepalive = keepalive   # seconds
        self.sampling_time = sampling_time  # seconds between manifests

        # Derived and hardware info
        self.RootPath = "/%s/" % name
        self.ip_addr = self.get_ip()
        self.mac_addr = self.get_mac()
        print("Got hw addr:", self.ip_addr, self.mac_addr)

        # Device list and types
        self.devices = []
        self.VALID_TYPES = []

        # Flags (replacing threading.Event)
        self.ack_event = False
        self.error_event = False
        self.timeout_event = False
        self.stop_event = False
        self.reconnect_event = False
        self.updt_event = False

        # MQTT client and timers
        self.client = None
        self.last_payload_time = time.ticks_ms()
        self.timeout_ack = 6000  # milliseconds
        self.sampling_time_ms = int(self.sampling_time * 1000)

    # ---------- MQTT client init ----------
    def __init_mqtt_client__(self):
        self.client = MQTTClient(self.Name, self.mqtt_broker, self.mqtt_port, keepalive=self.mqtt_keepalive)
        self.client.set_callback(self._on_message)

    # ---------- Safe wrappers ----------
    def safe_subscribe(self, topic):
        try:
            if self.client is None:
                return False
            self.client.subscribe(topic)
            return True
        except OSError as e:
            print("subscribe failed", topic, e)
            return False
        except Exception as e:
            print("subscribe unexpected error", topic, e)
            return False

    def safe_publish(self, topic, payload):
        try:
            if self.client is None:
                return False
            self.client.publish(topic, payload)
            return True
        except OSError as e:
            print("publish failed", topic, e)
            return False
        except Exception as e:
            print("publish unexpected error", topic, e)
            return False

    # ---------- Registration and ack ----------
    def acknowledge(self):
        if self.client is None:
            self.__init_mqtt_client__()
        print("starting client mqtt")
        self.client.connect()
        self._register_node()

    def _register_node(self):
        # Subscribe ack path and send validation request
        self.ack_path = self.ip_addr + "/" + self.Name + "/ack"
        register_request = {
            "Name": self.Name,
            "AcknowledgePath": self.ack_path,
            "MacAddress": self.mac_addr
        }
        print("ack payload:", register_request)
        self.safe_subscribe(self.ack_path)
        self.safe_publish("/node_name_request", json.dumps(register_request))

    # ---------- Message handling ----------
    def _on_message(self, topic, msg):
        try:
            messageValue = msg.decode("utf-8")
        except Exception:
            messageValue = str(msg)
        tstr = topic.decode() if isinstance(topic, bytes) else str(topic)
        print("registration response", messageValue, "for", tstr)

        if tstr == getattr(self, "ack_path", ""):
            try:
                serverResponse = json.loads(messageValue)
                result = serverResponse.get("result", "")
                self.VALID_TYPES = serverResponse.get("valid_types", [])
            except Exception as e:
                print("Invalid ack payload", e)
                self.error_event = True
                return

            if len(self.VALID_TYPES) == 0 or result in ["", "ERR_ACK"]:
                self.error_event = True
            elif result == "SUCCESS_ACK":
                self.ack_event = True
                self.reconnect_event = False
                self.timeout_event = False
                self.updt_event = True
                self._resubscribe_devices()
                # ensure immediate payload and reset timers
                self.last_payload_time = time.ticks_ms()
        else:
            target_device = self._get_subscriber_callback(tstr)
            if target_device:
                try:
                    print("Exec command:", messageValue, "for device", target_device["Name"])
                    target_device["command_callback"](messageValue)
                except Exception as e:
                    print("device command callback error", e)
            else:
                print("Unknown device topic", tstr)

    # ---------- Main polling loop ----------
    def loop(self):
        # ensure client exists and is initialized
        if self.client is None:
            try:
                self.__init_mqtt_client__()   # sets callback
                self.client.connect()
                self._register_node()
            except Exception as e:
                print("Initial connect failed:", e)
                time.sleep_ms(2000)
                return

        try:
            self.check_ack_timeout()
            # process incoming messages (raises OSError on disconnect)
            self.client.check_msg()
        except OSError as e:
            print("MQTT disconnected:", e)
            self.reconnect_event = True
            self._try_reconnect()
        except Exception as e:
            print("MQTT loop error:", e)

        # scheduled payload (sampling_time is in seconds)
        if self.ack_event and not self.stop_event:
            if time.ticks_diff(time.ticks_ms(), self.last_payload_time) >= self.sampling_time_ms:
                # free memory before building large JSON
                try:
                    gc.collect()
                except Exception:
                    pass
                self._build_and_send_payload_manifest()
                self.last_payload_time = time.ticks_ms()

        # small yield to avoid busy loop when called in tight main loop
        time.sleep_ms(10)

    # ---------- Reconnect logic ----------
    def _try_reconnect(self, max_attempts=5):
        for attempt in range(1, max_attempts + 1):
            # ensure WiFi is up first
            sta = network.WLAN(network.STA_IF)
            if not sta.isconnected():
                print("WiFi not connected, waiting")
                time.sleep_ms(2000)
                continue
            try:
                # re-init client if needed
                if self.client is None:
                    self.__init_mqtt_client__()
                self.client.connect()
                # re-register so server subscribes ack_path and knows us
                self._register_node()
                # resubscribe device topics
                self._resubscribe_devices()
                print("Reconnected on attempt", attempt)
                self.reconnect_event = False
                # reset timers so first payload goes out quickly
                self.last_payload_time = time.ticks_ms()
                return True
            except Exception as e:
                print("Reconnect failed attempt", attempt, ":", e)
                # exponential backoff with cap and small jitter
                backoff_ms = min(5000 + attempt * 2000, 30000)
                jitter = urandom.getrandbits(8) % 1000
                time.sleep_ms(backoff_ms + jitter)
        return False

    # ---------- Ack timeout ----------
    def check_ack_timeout(self):
        if not self.ack_event:
            if time.ticks_diff(time.ticks_ms(), self.last_payload_time) > self.timeout_ack:
                print("Ack timeout, scheduling reconnect")
                self.reconnect_event = True

    # ---------- Shutdown ----------
    def disable(self):
        self.stop_event = True
        try:
            if self.client is not None:
                self.client.disconnect()
            self.client = None
        except Exception:
            pass
        print("MQTT client stopped")

    # ---------- Manifest publish ----------
    def _build_and_send_payload_manifest(self):
        manifest = {
            "Name": self.Name,
            "RootName": self.RootPath,
            "ip": self.ip_addr,
            "mac_addr": self.mac_addr,
            "acknowledge_path": getattr(self, "ack_path", ""),
            "Devices": []
        }
        for device in self.devices:
            snapshot = dict(device)
            try:
                snapshot["Value"] = device["value_callback"]()
            except Exception as e:
                print("value callback error for", device.get("Name"), e)
                snapshot["Value"] = None
            snapshot.pop("value_callback", None)
            snapshot.pop("command_callback", None)
            manifest["Devices"].append(snapshot)

        payload = json.dumps(manifest)
        print("Publishing manifest:", payload)
        self.safe_publish("/inbound", payload)

    # ---------- Device utilities ----------
    def device_exists(self, name):
        if not self.ack_event:
            print("ERROR: No acknowledge finished")
            return False
        for device in self.devices:
            if device["Name"] == name:
                return True
        return False
    
    '''
    gets device from name, None if not found
    '''
    def get_device(self, name):
        if not self.ack_event:
            print("ERROR: No acknowledge finished")
            return False
        for device in self.devices:
            if device["Name"] == name:
                return device
        return None
    
    '''
    creates a quick event in mqtt instead of relying on the mqtt periodic manifest update
    usefull for direct response oriented flows like rfid door scans
    '''
    def send_event(self, name, value):
        if not self.ack_event:
            print("ERROR: No acknowledge finished")
            return False
        if self.client is None:
            print("ERROR: Client not available")
            return False
        
        device = self.get_device(name)

        if device is None:
            print("ERROR: Device not found")
            return False
                
        if device["Mode"] != "PUBLISHER":
            print("ERROR: Device is not  a publiser")
            return False

        payload = {
            "Name":name,
            "Mode":"PUBLISHER",
            "Type": device["Type"],
            "Channel": device["Channel"], #not in use considered new approach, leaved for legacy compatibility
            "Value": value
        }

        self.safe_publish(device["Channel"], payload)
        return True

    def _validate_device(self, name, type, get_value_call):
        if not self.ack_event:
            print("ERROR: No acknowledge finished")
            return
        if not name:
            raise ValueError("invalid name")
        if not type or type not in self.VALID_TYPES:
            raise ValueError("invalid type %s" % type)
        if get_value_call is None:
            raise ValueError("must provide a valid function")

    def add_publisher_device(self, name, type, get_value_callback):
        if self.device_exists(name):
            raise RuntimeError("Device name %s already exists" % name)
        self._validate_device(name, type, get_value_callback)
        publisher = {
            "Name": name,
            "Mode": "PUBLISHER",
            "Type": type,
            "Channel": self.RootPath + name + "/value",
            "value_callback": get_value_callback
        }
        self.devices.append(publisher)

    def add_subscriber_device(self, name, type, get_value_callback, command_callback):
        if self.device_exists(name):
            raise RuntimeError("Device name %s already exists" % name)
        self._validate_device(name, type, get_value_callback)
        channel_path = self.RootPath + name + "/value"
        subscriber = {
            "Name": name,
            "Mode": "SUBSCRIBER",
            "Type": type,
            "Channel": channel_path,
            "value_callback": get_value_callback,
            "command_callback": command_callback
        }
        self.safe_subscribe(channel_path)
        self.devices.append(subscriber)

    def _get_subscriber_callback(self, topic):
        for device in self.devices:
            if device["Channel"] == topic and device["Mode"] == "SUBSCRIBER":
                return device
        return None

    def _resubscribe_devices(self):
        for device in self.devices:
            if device["Mode"] == "SUBSCRIBER":
                self.safe_subscribe(device["Channel"])

    def remove_device(self, name):
        print("removing device %s" % name)
        for device in list(self.devices):
            if name == device["Name"]:
                print("removed device %s" % name)
                self.devices.remove(device)
                break
