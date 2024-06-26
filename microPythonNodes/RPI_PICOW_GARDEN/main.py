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

def initI2c():
    i2c1 = I2C(0 ,sda=Pin(I2C1_SDA_PIN), scl=Pin(I2C1_SCL_PIN), freq=I2C1_CLK_F)
    i2c2 = I2C(1 ,sda=Pin(I2C2_SDA_PIN), scl=Pin(I2C2_SCL_PIN), freq=I2C2_CLK_F)
    return i2c1, i2c2

def initDS1307(i2c):
    dsclk = DS1307(i2c)
    dsclk.halt(0)
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

manifest = {
        "Name":"MenyGarden2",
        "RootName":"/MenyGarden2/",
        "Devices":["waterLowLevel",
                   "photoResistor",
                   "moistureSensor",
                   "temperature",
                   "presure",
                   "altitude",
                   "waterTemperature",
                   "state",
                   "waterPump",
                   "timeOn",
                   "timeOff",
                   "dateTime",
                   "outputRelay1",
                   "outputRelay2",
                   "outputRelay3"
                   ]
}
jsonManifest = json.dumps(manifest)

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

def readBmp180(bmpSensor):
    return bmpSensor.temperature, bmpSensor.pressure, bmpSensor.altitude

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

def initSubscribers(client):
    subscribe(client, "/MenyGarden2/state/value")
    subscribe(client, "/MenyGarden2/timeOn/value")
    subscribe(client, "/MenyGarden2/timeOff/value")
    subscribe(client, "/MenyGarden2/waterPump/value")
    subscribe(client, "/MenyGarden2/dateTime/value")
    subscribe(client, "/MenyGarden2/outputRelay1/value")
    subscribe(client, "/MenyGarden2/outputRelay2/value")
    subscribe(client, "/MenyGarden2/outputRelay3/value")
    

def baseMQTTCallback(topic, msg):
    #this callback is to be called when message arrived to subscribed topics
    configsS = jsonfile("./configs.json")
    configsS.get_data()
    #a proper data validation should be performed here
    print('received from: ' + str(topic) + 'msg: ' + str(msg))
    
    if topic == b'/MenyGarden2/state/value':
        configObj = configsS.get_data()
        configObj["state"] = msg.decode("utf-8")
        print('state updated')
        configsS.update_data_dict(configObj)
        configsS.store_data()
    if topic == b'/MenyGarden2/timeOn/value':
        configObj = configsS.get_data()
        configObj["timeOn"] = msg.decode("utf-8")
        configsS.update_data_dict(configObj)
        configsS.store_data()
    if topic == b'/MenyGarden2/timeOff/value':
        configObj = configsS.get_data()
        configObj["timeOff"] = msg.decode("utf-8")
        configsS.update_data_dict(configObj)
        configsS.store_data()
    if topic == b'/MenyGarden2/waterPump/value':
        configObj = configsS.get_data()
        if configObj["state"] == "manual":
            setPump(int(msg))
    if topic == b'/MenyGarden2/dateTime/value':
        setDateTime(dsClock, msg.decode("utf-8"))
    if topic == b'/MenyGarden2/outputRelay1/value':
        setOutput("outputRelay1", int(msg))
    if topic == b'/MenyGarden2/outputRelay2/value':
        setOutput("outputRelay2", int(msg))
    if topic == b'/MenyGarden2/outputRelay3/value':
        setOutput("outputRelay3", int(msg))
    pass

#    my_jsonfile = jsonfile("./test.json", default_data = {"a": "porty", "b": "portx"})
#    print(my_jsonfile.get_data())
#    update_data = {"c": "portc", "b": "portb"}
#    my_jsonfile.update_data_dict(update_data)
#    print(my_jsonfile.get_data())
#    my_jsonfile.store_data()

def publishData(client, gpiosObj, bmpSensorObj, analogSensors, dsSensor, dsDevices, data):
    publish(client, manifest["RootName"]+"manifest",manifest)
    mqx_tmp =  {
        "Name":"waterLowLevel",
        "Mode":"PUBLISHER",
        "Type":"STRING",
        "Channel":manifest["RootName"] + "waterLowLevel",
        "Value":str(getLowLevelState())
    }
    jsonMsg = json.dumps(mqx_tmp)
    publish(client, manifest["RootName"] + "waterLowLevel", jsonMsg)

    
    mqx_tmp =  {
        "Name":"photoResistor",
        "Mode":"PUBLISHER",
        "Type":"STRING",
        "Channel":manifest["RootName"] + "photoResistor",
        "Value":str(readPhotoresistor(analogSensors))
    }
    jsonMsg = json.dumps(mqx_tmp)
    publish(client, manifest["RootName"] + "photoResistor", jsonMsg)

    mqx_tmp =  {
        "Name":"moistureSensor",
        "Mode":"PUBLISHER",
        "Type":"STRING",
        "Channel":manifest["RootName"] + "moistureSensor",
        "Value":str(readMoisture(analogSensors))
    }
    jsonMsg = json.dumps(mqx_tmp)
    publish(client, manifest["RootName"] + "moistureSensor", jsonMsg)

    temp, press, alt = readBmp180(bmpSensorObj)
    mqx_tmp =  {
        "Name":"temperature",
        "Mode":"PUBLISHER",
        "Type":"STRING",
        "Channel":manifest["RootName"] + "temperature",
        "Value":str(temp)
    }
    jsonMsg = json.dumps(mqx_tmp)
    publish(client, manifest["RootName"] + "temperature", jsonMsg)
    mqx_tmp =  {
        "Name":"pressure",
        "Mode":"PUBLISHER",
        "Type":"STRING",
        "Channel":manifest["RootName"] + "pressure",
        "Value":str(press)
    }
    jsonMsg = json.dumps(mqx_tmp)
    publish(client, manifest["RootName"] + "pressure", jsonMsg)
    mqx_tmp =  {
        "Name":"altitude",
        "Mode":"PUBLISHER",
        "Type":"STRING",
        "Channel":manifest["RootName"] + "altitude",
        "Value":str(alt)
    }
    jsonMsg = json.dumps(mqx_tmp)
    publish(client, manifest["RootName"] + "altitude", jsonMsg)
    
    mqx_tmp =  {
        "Name":"water temperature",
        "Mode":"PUBLISHER",
        "Type":"STRING",
        "Channel":manifest["RootName"] + "waterTemperature",
        "Value":str(readDS18X20(dsSensor, dsDevices, 0))
    }
    jsonMsg = json.dumps(mqx_tmp)
    publish(client, manifest["RootName"] + "waterTemperature", jsonMsg)
    
    mqx_tmp =  {
        "Name":"water Pump",
        "Mode":"SUBSCRIBER",
        "Type":"STRING",
        "Channel":"/MenyGarden2/waterPump/value",
        "Value":str(getPump())
    }
    jsonMsg = json.dumps(mqx_tmp)
    publish(client, manifest["RootName"] + "waterPump", jsonMsg)

    mqx_tmp =  {
        "Name":"state",
        "Mode":"SUBSCRIBER",
        "Type":"STRING",
        "Channel":"/MenyGarden2/state/value",
        "Value":data["state"]
    }
    jsonMsg = json.dumps(mqx_tmp)
    publish(client, manifest["RootName"] + "state", jsonMsg)
    mqx_tmp =  {
        "Name":"time on",
        "Mode":"SUBSCRIBER",
        "Type":"STRING",
        "Channel":"/MenyGarden2/timeOn/value",
        "Value":data["timeOn"]
    }
    jsonMsg = json.dumps(mqx_tmp)
    publish(client, manifest["RootName"] + "timeOn", jsonMsg)
    mqx_tmp =  {
        "Name":"time off",
        "Mode":"SUBSCRIBER",
        "Type":"STRING",
        "Channel": manifest["RootName"] + "timeOff" + "/value",
        "Value":data["timeOff"]
    }
    jsonMsg = json.dumps(mqx_tmp)
    publish(client, manifest["RootName"] + "timeOff", jsonMsg)    
    mqx_tmp =  {
        "Name":"outputRelay1",
        "Mode":"SUBSCRIBER",
        "Type":"STRING",
        "Channel": manifest["RootName"] + "outputRelay1" + "/value",
        "Value":str(getOutput("outputRelay1"))
    }
    jsonMsg = json.dumps(mqx_tmp)
    publish(client, manifest["RootName"] + "outputRelay1", jsonMsg)    
    mqx_tmp =  {
        "Name":"outputRelay2",
        "Mode":"SUBSCRIBER",
        "Type":"STRING",
        "Channel": manifest["RootName"] + "outputRelay2" + "/value",
        "Value":str(getOutput("outputRelay2"))
    }
    jsonMsg = json.dumps(mqx_tmp)
    publish(client, manifest["RootName"] + "outputRelay2", jsonMsg)   
    mqx_tmp =  {
        "Name":"outputRelay3",
        "Mode":"SUBSCRIBER",
        "Type":"STRING",
        "Channel": manifest["RootName"] + "outputRelay3" + "/value",
        "Value":str(getOutput("outputRelay3"))
    }
    jsonMsg = json.dumps(mqx_tmp)
    publish(client, manifest["RootName"] + "outputRelay3", jsonMsg)   
    pass

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
        temp, press, alt = readBmp180(bmpSensorObj)
        lcdObj.text('Sensors 1/3', 0, 0)
        lcdObj.text('Tw:'+ str(readDS18X20(dsSensor, dsDevices, 0)), 0, 10)
        lcdObj.text('T:'+ str(temp), 0, 20)
    elif printIndex == 3:
        lcdObj.text('Sensors 2/3', 0, 0)
        lcdObj.text('Ms:'+ str(readMoisture(analogSensors)), 0, 10)
        lcdObj.text('Pr:'+ str(readPhotoresistor(analogSensors)), 0, 20)
    elif printIndex == 4:
        temp, press, alt = readBmp180(bmpSensorObj)
        lcdObj.text('Sensors 3/3', 0, 0)
        lcdObj.text('P:'+ str(press), 0, 10)
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
	
	bmpSensorObj = initBmp(i2c1)
	oled = initOLED(i2c2)
	analogSensors = initADCs()
	gpiosObj = initGPIOS()
	dsSensor, dsDevices = initDS18X20(DS18X20_SENSOR_PIN)
	oled.text("connecting...", 0, 0)
	oled.show()
	wlanObj = wlanConnect(data["wifi_ssid"], data["wifi_pwd"])
	client = connectMQTT(data["mqtt_client_id"], data["mqtt_broker"], baseMQTTCallback)
	initSubscribers(client)
	printIndex = 0
    # OTA Block update
    filenames = ["main.py","micropython_ota.py","simple.py","bmp180.py","ds1307.py","ssd1306.py","jsonConfigs.py"]
    micropython_ota.ota_update(data["ota_host_url"], data["ota_project_name"], filenames, use_version_prefix=False, hard_reset_device=True, soft_reset_device=False, timeout=5)
    networkLock = _thread.allocate_lock()
    _thread.start_new_thread(update_task, (data,networkLock,)) #start second core thread
    wdt = WDT(timeout=7700) # is this a good approach
    # if no updates, proceed to the main routine

	while True:
        configsS.load_file()
		data = configsS.get_data()
        networkLock.acquire()
		client.check_msg()
		publishData(client, gpiosObj, bmpSensorObj, analogSensors, dsSensor, dsDevices, data)
        networkLock.release()
		printStates(oled, wlanObj, gpiosObj, bmpSensorObj, analogSensors, data, ds, dsSensor, dsDevices, printIndex)
		printIndex  = printIndex + 1
		if printIndex > printIndexCount:
			printIndex = 0
        wdt.feed()
		time.sleep(5)
	pass

'''
if __name__ == "__main__":
    idState = 0
    global configs
    global dsClock
    configs = jsonfile("./configs.json")
    configs.get_data()

    oledI2c = initOLED(LCD_SDA_PIN,LCD_SCL_PIN)
    bmpSensorObj = initBmp(BMP_180_I2C_ID, BMP_180_I2C_BAUD)
    gpiosObj = initGPIOS()
    dsSensor = initDS18X20(DS18X20_SENSOR_PIN)
    analogSensors = initADCs()
    dsClock = initDS3231(DS_CLOCK_SDA_PIN, DS_CLOCK_SCL_PIN)

    wlanObj = wlanConnect(ssid, password)
    client = connectMQTT(client_id, broker_server, baseMQTTCallback)
    initSubscribers(client)

    while True:
        printIndex  = printIndex + 1
        if printIndex > printIndexCount:
            printIndex = 0
        client.check_msg()
    pass

        configs.load_file()
        data = configs.get_data()
        publishData(client, gpiosObj, bmpSensorObj, dsSensor, analogSensors, data)

        printStates(oledI2c, wlanObj, gpiosObj, bmpSensorObj, dsSensor, analogSensors, data, dsClock, printIndex)

        if data["state"] == "auto" and getLowLevelState(gpiosObj) and timeInRange(dsClock.datetime(),data["timeOn"],data["timeOff"]):
            setPump(gpiosObj, True)
        else:
            setPump(gpiosObj, False)
        utime.sleep(4)
    pass
'''
