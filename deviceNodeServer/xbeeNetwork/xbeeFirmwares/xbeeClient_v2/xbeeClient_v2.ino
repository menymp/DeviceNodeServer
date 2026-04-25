/*
  DeviceMain.ino
  Example sketch that uses the XbeeDeviceBridge files above.
  Requires:
    - Andrew Rapp xbee-arduino (install via Library Manager or place in libraries/)
    - ArduinoJson v6
*/

#include <XBee.h>                 // Andrew Rapp library
#include "XbeeDeviceBridge.h"

// XBee objects
XBee xbee; // concrete XBee object used by transport
XBeeTransport transport(&xbee, &Serial, 9600);
XbeeDeviceBridge bridge(&transport);

float pirValue = 69.69;
String pumpState = "OFF";
unsigned long lastEventMs = 0;

String readPirSensor_cb(void *ctx) {
  pirValue += 0.1;
  if (pirValue > 100.0) pirValue = 69.69;
  char buf[16];
  dtostrf(pirValue, 0, 2, buf);
  return String(buf);
}

String readPumpState_cb(void *ctx) {
  return pumpState;
}

void pumpCommand_cb(const String &value, void *ctx) {
  if (value == "ON") digitalWrite(13, HIGH);
  else if (value == "OFF") digitalWrite(13, LOW);
  pumpState = value;
}

void setup() {
  pinMode(13, OUTPUT);
  digitalWrite(13, LOW);
  Serial.begin(115200);
  delay(100);

  // Initialize bridge and transport
  bridge.begin(9600);

  // Register devices
  bridge.addPublisher("PirSensor", "STRING", readPirSensor_cb, nullptr);
  bridge.addSubscriber("WaterPump", "STRING", readPumpState_cb, nullptr, pumpCommand_cb, nullptr);

  // Send manifest periodically
  bridge.setManifestIntervalMs(10000);
  bridge.sendManifest();
}

void loop() {
  bridge.loop();

  unsigned long now = millis();
  if (now - lastEventMs > 5000) {
    String val = readPirSensor_cb(nullptr);
    bridge.sendEvent("PirSensor", val.c_str());
    lastEventMs = now;
  }

  delay(10);
}
