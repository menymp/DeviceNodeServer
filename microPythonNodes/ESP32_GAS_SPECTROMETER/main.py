from machine import Pin, ADC 
import time

from simple import MQTTClient
import network

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

if __name__ == "__main__":
    analogSensors = initADCs()

    wlanConnect(ssid, password)
    client = connectMQTT(client_id, broker_server, baseMQTTCallback)
    
    #ToDo: add this as part of the reconfiguration ini file
    #      add main logic
    manifest = {
        "Name":"MenyGarden2",
        "RootName":"/MenyGarden2/",
        "Devices":["waterLowLevel","waterPump","photoResistor","moistureSensor","temperature","altitude","altitude","timeRange"]
    }
    exampleSensor =  {
        "Name":"water low level",
        "Mode":"PUBLISHER",
        "Type":"STRING",
        "Channel":"/MenyGarden2/waterLowLevel",
        "Value":"OFF"
    }

    while True:

        client.check_msg()
    pass