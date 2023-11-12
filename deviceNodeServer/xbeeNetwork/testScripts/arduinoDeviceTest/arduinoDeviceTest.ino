/*
 * menymp
 * Simple script to uploat to arduino that emulates a device for the xbee network
 * nov 2023
 */
#include <XBee.h>

XBee xbee = XBee();
XBeeResponse response = XBeeResponse();
// create reusable response objects for responses we expect to handle 
Rx16Response rx16 = Rx16Response();
Rx64Response rx64 = Rx64Response();


const int sensorAnalogPin = 0;
const int outputPin = 13;
int cnt = 0;
uint8_t data = 0;
uint8_t option = 0;

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
      } 
      else 
      {
        xbee.getResponse().getRx64Response(rx64);
        option = rx64.getOption();
        data = rx64.getData(0);
      }

      if(data == 'a') digitalWrite(outputPin, HIGH);
      if(data == 'b') digitalWrite(outputPin, LOW);
    }
  }
  if(cnt > 600)
  {
    String bufferOut = "sensorRead:" + String(analogRead(sensorAnalogPin)) + ",output:" + String(digitalRead(outputPin)) + "\n";
    Tx16Request tx = Tx16Request(0x1874, bufferOut.c_str(), bufferOut.length()); //ToDo: set modem address as static
    xbee.send(tx);
    cnt = 0;
  }
  cnt ++;
  delay(10);
}
