/*
 * menymp
 * Simple script to uploat to arduino that emulates a device for the xbee network
 * nov 2023
 * IMPORTANT: XBEE library works only with AP 2 mode
 */
#include <XBee.h>

XBee xbee = XBee();
XBeeResponse response = XBeeResponse();
// create reusable response objects for responses we expect to handle 
Rx16Response rx16 = Rx16Response();
Rx64Response rx64 = Rx64Response();

//XBeeAddress64 addr64 = XBeeAddress64(0x00000000, 0x00000000);
const int sensorAnalogPin = 0;
const int outputPin = 13;
int cnt = 0;
uint8_t data = 0;
uint8_t option = 0;
int request_len = 0;

void setup() {
  pinMode(outputPin,OUTPUT);
  Serial.begin(9600);
  xbee.setSerial(Serial);
  digitalWrite(outputPin, LOW);
}

void loop() {
  xbee.readPacket(100);
  if(xbee.getResponse().isAvailable())
  {
    if (xbee.getResponse().getApiId() == RX_16_RESPONSE || xbee.getResponse().getApiId() == RX_64_RESPONSE) 
    {
      // got a rx packet
      if (xbee.getResponse().getApiId() == RX_16_RESPONSE) 
      {
        xbee.getResponse().getRx16Response(rx16);
        option = rx16.getOption();
        data = rx16.getData(0);
        request_len = 16;
      } 
      else 
      {
        xbee.getResponse().getRx64Response(rx64);
        option = rx64.getOption();
        data = rx64.getData(0);
        request_len = 64;
      }

      if(data == 'a') digitalWrite(outputPin, HIGH);
      if(data == 'b') digitalWrite(outputPin, LOW);

      //digitalWrite(outputPin,!digitalRead(outputPin));
      if(request_len == 64)
      {
        String bufferOut = "sensorRead:" + String(analogRead(sensorAnalogPin)) + ",output:" + String(digitalRead(outputPin)) + "\n";
        Tx64Request tx = Tx64Request(rx64.getRemoteAddress64(), bufferOut.c_str(), bufferOut.length());
        xbee.send(tx);
      }
      if(request_len == 16)
      {
        String bufferOut = "sensorRead:" + String(analogRead(sensorAnalogPin)) + ",output:" + String(digitalRead(outputPin)) + "\n";
        Tx16Request tx = Tx16Request(rx16.getRemoteAddress16(), bufferOut.c_str(), bufferOut.length()); 
        xbee.send(tx);
      }

    }
  }
  //delay(10);
}
