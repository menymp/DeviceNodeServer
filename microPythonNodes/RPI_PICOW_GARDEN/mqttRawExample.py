import network
import utime
from umqtt.simple import MQTTClient

ssid = "ssid"
password = "password"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.config(pm = 0xa11140) # Diable powersave mode
wlan.connect(ssid, password)

max_wait = 10
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

def connectMQTT():
    client = MQTTClient(client_id=b"kudzai_raspberrypi_picow",
    server=b"8fbadaf843514ef286a2ae29e80b15a0.s1.eu.hivemq.cloud",
    port=0,
    user=b"mydemoclient",
    password=b"passowrd",
    keepalive=7200,
    ssl=True,
    ssl_params={'server_hostname':'8fbadaf843514ef286a2ae29e80b15a0.s1.eu.hivemq.cloud'})
    client.connect()
    return client

def publish(client, topic, value):
    print(topic)
    print(value)
    client.publish(topic, value)
    print("publish Done")

client = connectMQTT()

while True:
    print(sensor_reading)
    #publish as MQTT payload
    publish('picow/temperature', "20")
    publish('picow/pressure', "0")
    publish('picow/humidity', "15")
    #delay 5 seconds
    utime.sleep(5)
