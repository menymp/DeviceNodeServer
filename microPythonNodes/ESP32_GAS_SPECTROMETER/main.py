from machine import Pin, ADC 
import utime

from simple import MQTTClient
import network

MQ3_PIN = 5
MQ4_PIN = 6
MQ6_PIN = 2
MQ7_PIN = 4
MQ8_PIN = 1
MQ135_PIN = 3

ssid = "ssid"
password = "password"
max_wait = 10
client_id = "ESP32_GAS_SPECTROMETER_MENY"
broker_server = ""

def wlanConnect(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm = 0xa11140) # Diable powersave mode
    wlan.connect(ssid, password)

    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        utime.sleep(1)

        #Handle connection error
        if wlan.status() != 3:
            raise RuntimeError('wifi connection failed')
        else:
            print('connected')
        status = wlan.ifconfig()
        print('ip = ' + status[0])

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
    mq3 = ADC(MQ3_PIN)
    mq4 = ADC(MQ4_PIN)
    mq6 = ADC(MQ6_PIN)
    mq7 = ADC(MQ7_PIN)
    mq8 = ADC(MQ8_PIN)
    mq135 = ADC(MQ135_PIN)

    analogSensors = {
        "mq3":mq3,
        "mq4":mq4,
        "mq6":mq6,
        "mq7":mq7,
        "mq8":mq8,
        "mq135":mq135
    }
    return analogSensors

if __name__ == "__main__":
    analogSensors = initADCs()

    wlanConnect(ssid, password)
    client = connectMQTT(client_id, broker_server, baseMQTTCallback)
    
    #ToDo: add this as part of the reconfiguration ini file
    #      add main logic
    manifest = {
        "Name":"MenyGarden2",
        "RootName":"/MenyGasNode1/",
        "Devices":["MQ3","MQ4","MQ6","MQ7","MQ8","MQ135"]
    }
    exampleSensor =  {
        "Name":"MQ3 Measure",
        "Mode":"PUBLISHER",
        "Type":"STRING",
        "Channel":"/MenyGasNode1/MQ3",
        "Value":"0"
    }
    

    while True:

        client.check_msg()
    pass