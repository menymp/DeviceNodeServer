import machine import Pin, ADC
import utime
 
potentiometer_value = machine.ADC(28)
 
while True:
    potreading = potentiometer_value.read_u16()     
    print("potADC: ",potreading)
    utime.sleep(0.1)