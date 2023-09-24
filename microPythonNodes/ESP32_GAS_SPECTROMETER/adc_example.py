# Complete project details at https://RandomNerdTutorials.com

from machine import Pin, ADC
from time import sleep
#is NOT possible to use adc2 while connected to wifi
pot = ADC(Pin(32)) #2 (always 0),4,12,13,14,15,25,26,27,   32
pot.atten(ADC.ATTN_11DB)       #Full range: 3.3v
pot1 = ADC(Pin(4)) #2 (always 0),4,12,13,14,15,25,26,27,   32
pot1.atten(ADC.ATTN_11DB)
pot2 = ADC(Pin(12)) #2 (always 0),4,12,13,14,15,25,26,27,   32
pot2.atten(ADC.ATTN_11DB)
pot3 = ADC(Pin(13)) #2 (always 0),4,12,13,14,15,25,26,27,   32
pot3.atten(ADC.ATTN_11DB)
pot4 = ADC(Pin(14)) #2 (always 0),4,12,13,14,15,25,26,27,   32
pot4.atten(ADC.ATTN_11DB)
pot5 = ADC(Pin(15)) #2 (always 0),4,12,13,14,15,25,26,27,   32
pot5.atten(ADC.ATTN_11DB)
pot6 = ADC(Pin(25)) #2 (always 0),4,12,13,14,15,25,26,27,   32
pot6.atten(ADC.ATTN_11DB)
pot7 = ADC(Pin(26)) #2 (always 0),4,12,13,14,15,25,26,27,   32
pot7.atten(ADC.ATTN_11DB)

while True:
  pot_value = pot.read()
  print(pot_value)
  pot_value = pot1.read()
  print(pot_value)
  pot_value = pot2.read()
  print(pot_value)
  pot_value = pot3.read()
  print(pot_value)
  pot_value = pot4.read()
  print(pot_value)
  pot_value = pot5.read()
  print(pot_value)
  pot_value = pot6.read()
  print(pot_value)
  pot_value = pot7.read()
  print(pot_value)
  sleep(0.1)