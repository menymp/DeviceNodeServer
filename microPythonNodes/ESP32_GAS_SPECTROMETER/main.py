from machine import Pin, ADC 
import utime
import time
import json
import _thread
from jsonConfigs import jsonfile
from simple import MQTTClient
import network
import micropython_ota

#Global constants
FW_VERSION = 1.0
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

manifest = {
        "Name":"MenyGasNode1",
        "RootName":"/MenyGasNode1/",
        "Devices":["MQ3","MQ4","MQ6","MQ7","MQ8","MQ135"] #
}
jsonManifest = json.dumps(manifest)


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

#NOTE: strings must be byte string
def connectMQTT(client_id, brokerServer, callback):
    client = MQTTClient(client_id=client_id,
    server=brokerServer,
    port=0,
    #user=b"mydemoclient",
    #password=b"passowrd",
    keepalive=7200,
    #ssl=True,
    #ssl_params={'server_hostname':'8fbadaf843514ef286a2ae29e80b15a0.s1.eu.hivemq.cloud'}
    )
    client.connect()
    client.set_callback(callback)
    return client

def publish(client, topic, value):
    client.publish(topic, value)

def subscribe(client, topic):
    client.subscribe(topic)

def baseMQTTCallback(topic, msg):
    #this callback is to be called when message arrived to subscribed topics
    pass

def initADCs():
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
    return analogSensors

def readMQSensor(analogSensors, name):
    #ToDo: if a conversion is needed, this is the place
    return analogSensors[name].read()  

def buildMQMsg(Name, Channel, value):
    mqx_tmp =  {
        "Name":Name,
        "Mode":"PUBLISHER",
        "Type":"STRING",
        "Channel":Channel,
        "Value":str(value)
    }
    jsonMsg = json.dumps(mqx_tmp)
    return jsonMsg

def publishData(client ,analogSensors):
    publish(client, manifest["RootName"] + "manifest", jsonManifest)

    for mqSensor in manifest["Devices"]:
        baseChanel = manifest["RootName"] + mqSensor
        read = readMQSensor(analogSensors, mqSensor)
        jsonObj = buildMQMsg(mqSensor, manifest["RootName"] + mqSensor, read)
        publish(client, baseChanel, jsonObj)
    pass

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
    #analogSensors = initADCs()
    print("connecting...")
    wlanObj = wlanConnect(data["wifi_ssid"], data["wifi_pwd"])
    client = connectMQTT(data["mqtt_client_id"], data["mqtt_broker"], baseMQTTCallback)
    print("successfuly connected!")
    # OTA Block update
    filenames = ["main.py","micropython_ota.py","simple.py","jsonConfigs.py"]
    micropython_ota.ota_update(data["ota_host_url"], data["ota_project_name"], filenames, use_version_prefix=False, hard_reset_device=True, soft_reset_device=False, timeout=5)
    #init a second thread that will check for updates at specific intervals
    networkLock = _thread.allocate_lock()
    _thread.start_new_thread(update_task, (data,networkLock,)) #start second core thread
    # if no updates, proceed to the main routine
    analogSensors = initADCs()
    while True:
        networkLock.acquire()
        client.check_msg()
        publishData(client, analogSensors)
        networkLock.release()
        utime.sleep(6)
    pass