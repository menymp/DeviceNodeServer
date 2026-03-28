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

micropython uOTA future

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

enclosure and wiring needs

Example:
'''
from machine import I2C, Pin, ADC, WDT 
import time
from ds1307 import DS1307
import utime
from bmp180 import BMP180
import onewire
import ds18x20
from ssd1306 import SSD1306_I2C
from simple import MQTTClient
import network
import json
import _thread
from jsonConfigs import jsonfile
import micropython_ota
from unode_bridge import node_bridge  # replace with actual module name

FW_VERSION = 1.0

max_wait = 10

#hw specific constants
I2C1_SDA_PIN = 0
I2C1_SCL_PIN = 1
I2C1_CLK_F = 200000
I2C2_SDA_PIN = 2
I2C2_SCL_PIN = 3
I2C2_CLK_F = 200000
WATER_PUMP_PIN = 25
LOW_WATER_SENSOR = 24
DS18X20_SENSOR_PIN = 22
PHOTORESISTOR_PIN = 27
MOISTURE_SENSOR_PIN = 26
GENERIC_OUTPUT1_PIN = 0
GENERIC_OUTPUT2_PIN = 0
GENERIC_OUTPUT3_PIN = 0

analogSensors = {}
GPIOs = {}

def initI2c():
    i2c1 = I2C(0 ,sda=Pin(I2C1_SDA_PIN), scl=Pin(I2C1_SCL_PIN), freq=I2C1_CLK_F)
    i2c2 = I2C(1 ,sda=Pin(I2C2_SDA_PIN), scl=Pin(I2C2_SCL_PIN), freq=I2C2_CLK_F)
    return i2c1, i2c2

def initDS1307(i2c):
    dsclk = DS1307(i2c)
    dsclk.halt(0)
    return dsclk

bmpSensorObj = None

def initBmp(i2c):
    global bmpSensorObj
    bmp180 = BMP180(i2c)
    bmp180.oversample_sett = 2
    bmp180.baseline = 101325
    pass

def initOLED(i2c):
    oled = SSD1306_I2C(128, 32, i2c)
    oled.fill(0)
    oled.show()
    return oled

configsS = None
dsClock = None
GPIOs = None

def setGlobals(configs, dsClk, GPIOs):
    global configsS
    global dsClock
    global GPIOs
    configsS = configs
    dsClock = dsClk
    

'''
year = 2020 # Can be yyyy or yy format
month = 10
mday = 3
hour = 13 # 24 hour format only
minute = 55
second = 30 # Optional
weekday = 6 # Optional

Call ds.datetime() to get the current date and time. This will print a warning on the REPL when the Oscillator Stop Flag (OSF) is set. When not using the REPL the OSF
'''
#expected str input format: 2023-07-23-1 16:30:43.320847
def setDateTime(dsClock, dateTimeStr):
    dateTimeList = dateTimeStr.split(' ')
    dateList = dateTimeList[0].split('-')
    timeList = dateTimeList[1].split(':')
    year = int(dateList[0])
    month = int(dateList[1])
    mday = int(dateList[2])
    wday = int(dateList[3])
    hour = int(timeList[0])
    minute = int(timeList[1])
    second = int(timeList[2])
    datetime = (year, month, mday, wday, hour, minute, second)
    dsClock.datetime(datetime)
    pass

def timeInRange(currentTime, timeOnStr, timeOffStr):
    onHour, onMin = parseTimeStr(timeOnStr)
    offHour, offMin = parseTimeStr(timeOffStr)

    #ToDo: For now use this, if in the future is expected to work in midnight shifts add proper handling
    if onHour <= currentTime[4] <= offHour and onMin <= currentTime[5] <= offMin:
        return True
    return False

def parseTimeStr(timeOnStr):
    timeOnList = timeOnStr.split(':')
    hour = int(timeOnList[0])
    min = int(timeOnList[0])
    return hour, min

def writeOLEDMsgs(oled, msgList):
    oled.fill(0)
    oled.show()
    for index in range(0, len(msgList)):
        oled.text(msgList[index][0] + " : "+msgList[index][1], 0, 10*index)
    oled.show()

def initGPIOS():
    #outputs
    waterPump = Pin(WATER_PUMP_PIN, mode=Pin.OUT)
    waterPump.value(0)
    outRelay1 = Pin(GENERIC_OUTPUT1_PIN, mode=Pin.OUT)
    outRelay1.value(0)
    outRelay2 = Pin(GENERIC_OUTPUT2_PIN, mode=Pin.OUT)
    outRelay2.value(0)
    outRelay3 = Pin(GENERIC_OUTPUT3_PIN, mode=Pin.OUT)
    outRelay3.value(0)
    #inputs
    waterLowLevel = Pin(LOW_WATER_SENSOR, mode=Pin.IN, pull=Pin.PULL_UP)
    GPIOs = {
        "waterPump":waterPump,
        "waterLowLevel":waterLowLevel,
        "outputRelay1":outRelay1,
        "outputRelay2":outRelay2,
        "outputRelay3":outRelay3
    }
    return GPIOs

def initADCs():
    global analogSensors
    photoResistor = ADC(PHOTORESISTOR_PIN)
    moistureSensor = ADC(MOISTURE_SENSOR_PIN)
    analogSensors = {
        "photoResistor":photoResistor,
        "moistureSensor":moistureSensor
    }
    pass

def readPhotoresistor():
    #ToDo: if a conversion is needed, this is the place
    return analogSensors["photoResistor"].read_u16()  

def readMoisture():
    #ToDo: if a conversion is needed, this is the place
    return analogSensors["moistureSensor"].read_u16() 

def getWaterTemp():
    return readDS18X20(dsSensor, dsDevices, 0)

def readTemp():
    bmpSensorObj.temperature

def readPressure():
    bmpSensorObj.pressure

def readAltitude():
    bmpSensorObj.altitude

def setPump(value):
    GPIOs["waterPump"].value(value)

def getPump():
    return GPIOs["waterPump"].value()

def getOutput(name):
    return GPIOs[name].value()

def getOutput(name, value):
    return GPIOs[name].value(value)

def getLowLevelState():
    return GPIOs["waterLowLevel"].value()

def initDS18X20(pin=22):
    ow = onewire.OneWire(Pin(pin))
    ds = ds18x20.DS18X20(ow)
    utime.sleep_ms(750)
    devices = ds.scan()
    print('found devices:', devices)
    return ds, devices

def readDS18X20(ds, devices, index = 0):
    ds.convert_temp()
    utime.sleep_ms(750)
    return ds.read_temp(devices[index])

def wlanConnect(ssid, password):
    global max_wait
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm = 0xa11140) # Diable powersave mode
    wlan.connect(ssid, password)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.active(True)
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    return wlan

#a proper data validation should be performed in each callback
def setState(value):
    configObj = configsS.get_data()
    configObj["state"] = value.decode("utf-8")
    print('state updated')
    configsS.update_data_dict(configObj)
    configsS.store_data()

def setTimeOn(value):
    configObj = configsS.get_data()
    configObj["timeOn"] = value.decode("utf-8")
    configsS.update_data_dict(configObj)
    configsS.store_data()

def setTimeOff(value):
    configObj = configsS.get_data()
    configObj["timeOff"] = value.decode("utf-8")
    configsS.update_data_dict(configObj)
    configsS.store_data()

def setWaterPump(value):
    configObj = configsS.get_data()
    if configObj["state"] == "manual":
        setPump(int(value))

def setDateTimeRtc(value):
    setDateTime(dsClock, value.decode("utf-8"))

def setOutputRelay1(value):
    setOutput("outputRelay1", int(value))

def setOutputRelay2(value):
    setOutput("outputRelay2", int(value))

def setOutputRelay3(value):
    setOutput("outputRelay3", int(value))

def setOutput(output, value):
    GPIOs[output] = value

printIndexCount = 7

def printStates(lcdObj, wlan, gpiosObj, bmpSensorObj, analogSensors, data, dsClock, dsSensor, dsDevices, printIndex):
    lcdObj.fill(0)

    if printIndex == 0:
        lcdObj.text('Pico W Garden', 0, 0)
        lcdObj.text('version:' + str(FW_VERSION), 0, 10)
        lcdObj.text('IP:' + wlan.ifconfig()[0], 0, 20)
    elif printIndex == 1:
        lcdObj.text('IO States', 0, 0)
        lcdObj.text('P/O:'+ str(getPump()), 0, 10)
        lcdObj.text('L/I:'+ str(getLowLevelState()), 0, 20)
    elif printIndex == 2:
        lcdObj.text('Sensors 1/3', 0, 0)
        lcdObj.text('Tw:'+ str(readDS18X20(dsSensor, dsDevices, 0)), 0, 10)
        lcdObj.text('T:'+ str(bmpSensorObj.temperature), 0, 20)
    elif printIndex == 3:
        lcdObj.text('Sensors 2/3', 0, 0)
        lcdObj.text('Ms:'+ str(readMoisture(analogSensors)), 0, 10)
        lcdObj.text('Pr:'+ str(readPhotoresistor(analogSensors)), 0, 20)
    elif printIndex == 4:
        lcdObj.text('Sensors 3/3', 0, 0)
        lcdObj.text('P:'+ str(bmpSensorObj.pressure), 0, 10)
    elif printIndex == 5:
        lcdObj.text('Flags 1/1', 0, 0)
        lcdObj.text('S:' + data["state"], 0, 10)
    elif printIndex == 6:
        lcdObj.text('Timer 1/2', 0, 0)
        lcdObj.text('D:'+ str(dsClock.datetime()[0]) + '-' + str(dsClock.datetime()[1]) + '-' + str(dsClock.datetime()[2]), 0, 10)
        lcdObj.text('T:'+ str(dsClock.datetime()[4]) + ':' + str(dsClock.datetime()[5]) + ':' + str(dsClock.datetime()[6]), 0, 20)
    elif printIndex == 7:
        lcdObj.text('Timer 2/2', 0, 0)
        lcdObj.text('on:' + data["timeOn"], 0, 10)
        lcdObj.text('off:' + data["timeOff"], 0, 20)
    else:
        lcdObj.text('Pico W Garden', 0, 0)
        lcdObj.text('version:' + str(FW_VERSION), 0, 10)
        lcdObj.text('IP:' + wlan.ifconfig()[0], 0, 20)
    lcdObj.show()
    pass

#this task checks for available updates
#       flags for safe before reset       PENDING
def update_task(configs, networkLock):
    while(True):
        utime.sleep(20)
        networkLock.acquire()
        micropython_ota.check_for_ota_update(configs["ota_host_url"], configs["ota_project_name"], soft_reset_device=False, timeout=5)
        networkLock.release()

if __name__ == "__main__":
	idState = 0
	
	configsS = jsonfile("./configs.json")
	data = configsS.get_data()
	gpiosObj = initGPIOS()
	i2c1, i2c2 = initI2c()
	ds = initDS1307(i2c1)
	setGlobals(configsS, ds, gpiosObj) 
	
	initBmp(i2c1)
	oled = initOLED(i2c2)
	analogSensors = initADCs()
	gpiosObj = initGPIOS()
	dsSensor, dsDevices = initDS18X20(DS18X20_SENSOR_PIN)
	oled.text("connecting...", 0, 0)
	oled.show()
	wlanObj = wlanConnect(data["wifi_ssid"], data["wifi_pwd"])
	
	bridge = node_bridge(name="MenyGarden2", broker=data["mqtt_broker"], port=data["mqtt_port"],
	                     keepalive=60, sampling_time=6)
	time.sleep(3)

	bridge.add_publisher_device("waterLowLevel", "FLOAT", getLowLevelState)  # Event needed
	bridge.add_publisher_device("photoResistor", "FLOAT", readPhotoresistor)
	bridge.add_publisher_device("moistureSensor", "FLOAT", readMoisture)
	bridge.add_publisher_device("temperature", "FLOAT", readTemp)
	bridge.add_publisher_device("pressure", "FLOAT", readPressure)
	bridge.add_publisher_device("altitude", "FLOAT", readAltitude)
	bridge.add_publisher_device("waterTemperature", "FLOAT", getWaterTemp)

	def getState():
		data["state"]

	def getTimeOn():
		data["timeOn"]

	def getTimeOff():
		data["timeOff"]

	def getRelay1():
		getOutput("outputRelay1")

	def getRelay2():
		getOutput("outputRelay2")

	def getRelay3():
		getOutput("outputRelay3")

	bridge.add_subscriber_device("dateTime", "STRING", dsClock.datetime, setDateTimeRtc)
	bridge.add_subscriber_device("waterPump", "STRING", getPump, setWaterPump)
	bridge.add_subscriber_device("state", "STRING", getState, setState)
	bridge.add_subscriber_device("timeOn", "STRING", getTimeOn, setTimeOn)
	bridge.add_subscriber_device("timeOff", "STRING", getTimeOff, setTimeOff)
	bridge.add_subscriber_device("outputRelay1", "STRING", getRelay1, setOutputRelay1)
	bridge.add_subscriber_device("outputRelay2", "STRING", getRelay2, setOutputRelay2)
	bridge.add_subscriber_device("outputRelay3", "STRING", getRelay3, setOutputRelay3)

	printIndex = 0
	# OTA Block update
	filenames = ["main.py","micropython_ota.py","simple.py","bmp180.py","ds1307.py","ssd1306.py","jsonConfigs.py"]
	micropython_ota.ota_update(data["ota_host_url"], data["ota_project_name"], filenames, use_version_prefix=False, hard_reset_device=True, soft_reset_device=False, timeout=5)
	networkLock = _thread.allocate_lock()
	_thread.start_new_thread(update_task, (data,networkLock,)) #start second core thread
	wdt = WDT(timeout=7700) # is this a good approach
	# if no updates, proceed to the main routine
	cnt = 0
	while True:
		configsS.load_file()
		data = configsS.get_data()
		networkLock.acquire()
		if getLowLevelState():
			cnt = 0
			print("Event firing")
			bridge.send_event("waterLowLevel",getLowLevelState().encode('utf-8'))
		bridge.loop()
		networkLock.release()
		printStates(oled, wlanObj, gpiosObj, bmpSensorObj, analogSensors, data, ds, dsSensor, dsDevices, printIndex)
		printIndex  = printIndex + 1
		cnt = cnt + 1
		if printIndex > printIndexCount:
			printIndex = 0
		wdt.feed()
		time.sleep(0.05)
	pass

