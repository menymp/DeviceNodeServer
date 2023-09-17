'''
micropython example menymp July 2023

simple garden control

IO requeriments
OK    i2c bmp 180 sensor
OK    i2c lcd display
    i2c ds3231 RTC 
OK    2x analog chanels
OK        - moisture ground sensor
OK        - photoresistor
OK    2x GPIO pins
OK        - water low level
OK        - pump relay control
OK    ds18x20 water resistant temperature sensor
    
    mqtt communication
    config.json file capability

'''


'''
Wiring the sensor to the pyboard

| pyboard| bmp180 |
|:------:|:------:|
| VIN    | VIN    |
| 3V3    | 3Vo    |
| GND    | GND    |
| SCL    | SCL    |
| SDA    | SDA    |

Quickstart

Example:
'''
from machine import I2C, Pin, ADC 
import time
from ds1307 import DS1307
from bmp180 import BMP180
from ssd1306 import SSD1306_I2C
'''
import onewire
import ds18x20

from simple import MQTTClient
import network
'''

ssid = "ssid"
password = "password"
max_wait = 10
client_id = "PIPICO_GARDEN_MENY"
broker_server = ""

WATER_PUMP_PIN = 1
LOW_WATER_SENSOR = 2
BMP_180_I2C_ID = 1
BMP_180_I2C_BAUD = 100000
DS18X20_SENSOR_PIN = 28
PHOTORESISTOR_PIN = 29
MOISTURE_SENSOR_PIN = 30

def initI2c():
    i2c1 = I2C(0 ,sda=Pin(0), scl=Pin(1), freq=200000)
    i2c2 = I2C(1 ,sda=Pin(2), scl=Pin(3), freq=200000)
    return i2c1, i2c2

def initDS1307(i2c):
    dsclk = DS1307(i2c)
    return dsclk

def initBmp(i2c):
    bmp180 = BMP180(i2c)
    bmp180.oversample_sett = 2
    bmp180.baseline = 101325
    return bmp180

def initOLED(i2c):
    oled = SSD1306_I2C(128, 32, i2c)
    oled.fill(0)
    oled.show()
    return oled
'''
year = 2020 # Can be yyyy or yy format
month = 10
mday = 3
hour = 13 # 24 hour format only
minute = 55
second = 30 # Optional
weekday = 6 # Optional

datetime = (year, month, mday, hour, minute, second, weekday)
ds.datetime(datetime)

Call ds.datetime() to get the current date and time. This will print a warning on the REPL when the Oscillator Stop Flag (OSF) is set. When not using the REPL the OSF

ToDo: check alarms for the ON and OFF for the pump
'''

def writeOLEDMsgs(oled, msgList):
    oled.fill(0)
    oled.show()
    for index in range(0, len(msgList)):
        oled.text(msgList[index][0] + " : "+msgList[index][1], 0, 10*index)
    oled.show()

def readBmp180(bmpSensor):
    return bmpSensor.temperature, bmpSensor.pressure, bmpSensor.altitude

def initGPIOS():
    waterPump = Pin(WATER_PUMP_PIN, mode=Pin.OUT)
    waterPump.value(0)
    waterLowLevel = Pin(LOW_WATER_SENSOR, mode=Pin.IN, pull=Pin.PULL_UP)
    GPIOs = {
        "waterPump":waterPump,
        "waterLowLevel":waterLowLevel
    }
    return GPIOs

def initADCs():
    photoResistor = ADC(PHOTORESISTOR_PIN)
    moistureSensor = ADC(MOISTURE_SENSOR_PIN)
    analogSensors = {
        "photoResistor":photoResistor,
        "moistureSensor":moistureSensor
    }
    return analogSensors

def readPhotoresistor(analogSensors):
    #ToDo: if a conversion is needed, this is the place
    return analogSensors["photoResistor"].read_u16()  

def readMoisture(analogSensors):
    #ToDo: if a conversion is needed, this is the place
    return analogSensors["moistureSensor"].read_u16()  

def setPump(GPIOs, value):
    GPIOs["waterPump"].value(value)

def getLowLevelState(GPIOs):
    return GPIOs["waterLowLevel"].value()

def initDS18X20(pin=28):
    ow = onewire.OneWire(Pin(pin))
    ds = ds18x20.DS18X20(ow)
    devices = ds.scan()
    print('found devices:', devices)
    return ds, devices

def readDS18X20(ds, devices, index = 0):
    ds.convert_temp()
    time.sleep_ms(750)
    return ds.read_temp(devices[index])

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


#    my_jsonfile = jsonfile("./test.json", default_data = {"a": "porty", "b": "portx"})
#    print(my_jsonfile.get_data())
#    update_data = {"c": "portc", "b": "portb"}
#    my_jsonfile.update_data_dict(update_data)
#    print(my_jsonfile.get_data())
#    my_jsonfile.store_data()

def publishData():
    pass
	

if __name__ == "__main__":
	i2c1, i2c2 = initI2c()
	ds = initDS1307(i2c1)
	bmpSensorObj = initBmp(i2c1)
	oled = initOLED(i2c2)
	oled.text("test oled", 0, 0)
	oled.show()
	while True:
		print(ds.datetime())
		print(readBmp180(bmpSensorObj))
		time.sleep(1)
	pass

'''
if __name__ == "__main__":
    bmpSensorObj = initBmp(BMP_180_I2C_ID, BMP_180_I2C_BAUD)
    gpiosObj = initGPIOS()
    dsSensor = initDS18X20(DS18X20_SENSOR_PIN)
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
'''