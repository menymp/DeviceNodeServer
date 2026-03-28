from machine import Pin, ADC 
import utime
import time
from unode_bridge import node_bridge  # replace with actual module name
import _thread
from jsonConfigs import jsonfile
import network
import micropython_ota

#Global constants
FW_VERSION = 1.0
BROKER = "192.168.1.100"   # or broker hostname reachable from device
BROKER_PORT = 1883

'''
MQ2_PIN = 32
MQ3_PIN = 33
MQ4_PIN = 34
MQ6_PIN = 35
MQ7_PIN = 36
MQ8_PIN = 27
MQ135_PIN = 39
'''
#
# important note: pins 37 38 are internal and not externaly available
# ADC2 is not possible to be used while WIFI is connected, that leads to
# an error called invalid atten, or TIMEOUT
#MQ2_PIN = 32
MQ3_PIN = 32
MQ4_PIN = 33
MQ6_PIN = 34
MQ7_PIN = 35
MQ8_PIN = 36
#MQ9_PIN = 26
MQ135_PIN = 39

analogSensors = {}
max_wait = 10

def wlanConnect(ssid, password):
    global max_wait
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        wlan.active(True)
        wlan.connect(ssid, password)
        print('Connecting to: %s' % ssid)
        timeout = time.ticks_ms()
        while not wlan.isconnected():
            time.sleep(0.15)
            if (time.ticks_diff (time.ticks_ms(), timeout) > 15000):
                break
        if wlan.isconnected():
            print('Successful connection to: %s' % ssid)
            print('IP: %s\nSUBNET: %s\nGATEWAY: %s\nDNS: %s' % wlan.ifconfig()[0:4])
        else:
            wlan.active(False)
            print('Failed to connect to: %s' % ssid)
    else:
        print('Connected\nIP: %s\nSUBNET: %s\nGATEWAY: %s\nDNS: %s' % wlan.ifconfig()[0:4])
    return wlan

def initADCs():
    global analogSensors
    mq3 = ADC(Pin(MQ3_PIN))
    mq3.atten(ADC.ATTN_11DB)
    mq4 = ADC(Pin(MQ4_PIN))
    mq4.atten(ADC.ATTN_11DB)
    mq6 = ADC(Pin(MQ6_PIN))
    mq6.atten(ADC.ATTN_11DB)
    mq7 = ADC(Pin(MQ7_PIN))
    mq7.atten(ADC.ATTN_11DB)
    mq8 = ADC(Pin(MQ8_PIN))
    mq8.atten(ADC.ATTN_11DB)
    mq135 = ADC(Pin(MQ135_PIN))
    mq135.atten(ADC.ATTN_11DB)
    #in the future, an important sensor is mq9 for carbon monoxide
    analogSensors = {
        "MQ3":mq3,
        "MQ4":mq4,
        "MQ6":mq6,
        "MQ7":mq7,
        "MQ8":mq8,
        "MQ135":mq135
    }
    pass


# If there is a need for special conversions, each function is the place
def readMQ3():
    analogSensors["MQ3"].read()

def readMQ4():
    analogSensors["MQ4"].read() 

def readMQ6():
    analogSensors["MQ6"].read() 

def readMQ7():
    analogSensors["MQ7"].read() 

def readMQ8():
    analogSensors["MQ8"].read() 

def readMQ135():
    analogSensors["MQ135"].read()

#this task checks for available updates
# ToDo: add sync for the wifi shared UI   OK
#       flags for safe before reset       PENDING
def update_task(configs, networkLock):
    while(True):
        utime.sleep(20)
        networkLock.acquire()
        micropython_ota.check_for_ota_update(configs["ota_host_url"], configs["ota_project_name"], soft_reset_device=False, timeout=5)
        networkLock.release()
        

if __name__ == "__main__":
    configsS = jsonfile("./configs.json")
    data = configsS.get_data()
    print("connecting...")
    wlanObj = wlanConnect(data["wifi_ssid"], data["wifi_pwd"])
    print("successfuly connected!")
    # instantiate bridge (module must be on device filesystem)
    bridge = node_bridge(name="MenyGasNode1", broker=data["mqtt_broker"], port=data["mqtt_port"],
                         keepalive=60, sampling_time=6)
    
    bridge.acknowledge()

    # add mock devices after ack (the module enforces ack_event before adding)
    # if your implementation requires ack_event True before add, wait a short time
    time.sleep(3)
    bridge.add_publisher_device("MQ3", "STRING", readMQ3)
    bridge.add_publisher_device("MQ4", "STRING", readMQ4)
    bridge.add_publisher_device("MQ6", "STRING", readMQ6)
    bridge.add_publisher_device("MQ7", "STRING", readMQ7)
    bridge.add_publisher_device("MQ8", "STRING", readMQ8)
    bridge.add_publisher_device("MQ135", "STRING", readMQ135)

    # OTA Block update
    filenames = ["main.py","micropython_ota.py","simple.py","jsonConfigs.py"]
    micropython_ota.ota_update(data["ota_host_url"], data["ota_project_name"], filenames, use_version_prefix=False, hard_reset_device=True, soft_reset_device=False, timeout=5)
    #init a second thread that will check for updates at specific intervals
    networkLock = _thread.allocate_lock()
    _thread.start_new_thread(update_task, (data,networkLock,)) #start second core thread
    # if no updates, proceed to the main routine
    initADCs()
    cnt = 0
    while True:
        time.sleep(0.05)
        networkLock.acquire()
        
        bridge.loop()
        if cnt > 50:
            cnt = 0
            bridge.send_event("MQ3", str(readMQ3()).encode('utf-8'))
            bridge.send_event("MQ4", str(readMQ4()).encode('utf-8'))
            bridge.send_event("MQ6", str(readMQ6()).encode('utf-8'))
            bridge.send_event("MQ7", str(readMQ7()).encode('utf-8'))
            bridge.send_event("MQ8", str(readMQ8()).encode('utf-8'))
            bridge.send_event("MQ135", str(readMQ135()).encode('utf-8'))
        networkLock.release()
    pass