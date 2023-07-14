'''
micropython example menymp July 2023

simple garden control

IO requeriments
    i2c bmp 180 sensor
    i2c lcd display
    2x analog chanels
        - moisture ground sensor
        - photoresistor
    2x GPIO pins
        - water low level
        - pump relay control
    ds18x20 water resistant temperature sensor

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
from machine import Pin

pin = Pin(enable_Pin, mode=Pin.IN, pull=Pin.PULL_UP)
pin.value()
#bmp imports
from bmp180 import BMP180
from machine import I2C, Pin                        # create an I2C bus object accordingly to the port you are using
bus = I2C(1, baudrate=100000)           # on pyboard
# bus =  I2C(scl=Pin(4), sda=Pin(5), freq=100000)   # on esp8266
bmp180 = BMP180(bus)
bmp180.oversample_sett = 2
bmp180.baseline = 101325

temp = bmp180.temperature
p = bmp180.pressure
altitude = bmp180.altitude
print(temp, p, altitude)