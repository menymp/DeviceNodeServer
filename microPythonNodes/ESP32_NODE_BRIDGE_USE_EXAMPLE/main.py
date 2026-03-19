# main.py - ESP32 example using node_bridge module
import network
import time
from unode_bridge import node_bridge  # replace with actual module name

WIFI_SSID = "your_ssid"
WIFI_PASS = "your_password"
BROKER = "192.168.1.100"   # or broker hostname reachable from device
BROKER_PORT = 1883

def connect_wifi(ssid, password, timeout=15):
    sta = network.WLAN(network.STA_IF)
    if not sta.active():
        sta.active(True)
    if not sta.isconnected():
        print("Connecting to WiFi...")
        sta.connect(ssid, password)
        start = time.time()
        while not sta.isconnected():
            if time.time() - start > timeout:
                raise RuntimeError("WiFi connect timeout")
            time.sleep(0.5)
    print("WiFi connected:", sta.ifconfig())

# --- Mock device callbacks ---
def mock_temp_value():
    # return a fake temperature
    return 25.5

def mock_counter_value():
    # return a fake counter
    return 42

def pump_command_handler(payload):
    print("Pump command received:", payload)
    # implement actuator handling here

# --- Main ---
try:
    connect_wifi(WIFI_SSID, WIFI_PASS)
    
    halObj = network_utils_hal()
    print(halObj.get_ip())
    print(halObj.get_mac())

    # instantiate bridge (module must be on device filesystem)
    bridge = node_bridge(name="ESP32MockNode", broker=BROKER, port=BROKER_PORT,
                         keepalive=60, sampling_time=6)

    # initialize MQTT client and register with server
    bridge.acknowledge()

    # add mock devices after ack (the module enforces ack_event before adding)
    # if your implementation requires ack_event True before add, wait a short time
    time.sleep(1)

    # Add publisher devices
    try:
        bridge.add_publisher_device("TempSensor", "FLOAT", mock_temp_value)
        bridge.add_publisher_device("Counter", "INT", mock_counter_value)
    except Exception as e:
        print("Add publisher error:", e)

    # Add subscriber device (actuator)
    try:
        bridge.add_subscriber_device("PumpMotor", "STRING", lambda: "OFF", pump_command_handler)
    except Exception as e:
        print("Add subscriber error:", e)

    # Main polling loop
    print("Entering main loop. Press Ctrl+C to stop.")
    cnt = 0
    while True:
        bridge.loop()
        # small sleep to avoid tight loop; bridge.loop already yields, but keep safe
        time.sleep(0.05)
        if cnt > 50:
            cnt = 0
            print("Event firing")
            value = 70.70
            bridge.send_event("TempSensor", str(value).encode('utf-8'))
        cnt = cnt + 1

except KeyboardInterrupt:
    print("Interrupted by user, shutting down")
    try:
        bridge.disable()
    except Exception:
        pass
except Exception as e:
    print("Fatal error:", e)
