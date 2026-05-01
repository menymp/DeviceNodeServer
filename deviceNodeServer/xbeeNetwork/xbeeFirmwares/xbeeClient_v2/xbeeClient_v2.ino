/*
  DeviceMain.ino
  Compact comma protocol:
   - Manifest: M<count>:Name,Mode,Type,Value;...#
   - Event:   E:Name,Mode,Type,Value#
   - Command: C:Device,Value#
  Uses AltSoftSerial (RX=8, TX=9) and XBee API frames.
*/

#include <AltSoftSerial.h>
#include <XBee.h>
#include "XbeeDeviceBridge.h"

// AltSoftSerial (RX=8, TX=9)
AltSoftSerial xbeeSerial;
XBee xbee;
XBeeTransport transport(&xbee, &xbeeSerial, 9600);

// Set coordinator address (replace with your coordinator)
const char COORDINATOR_ADDR_STR[] = "...";
const uint64_t COORDINATOR_ADDR64 = (sizeof(COORDINATOR_ADDR_STR) > 1 && COORDINATOR_ADDR_STR[0] != '\0')
  ? XbeeDeviceBridge::parseHex64(COORDINATOR_ADDR_STR)
  : 0ULL;

XbeeDeviceBridge bridge(&transport, COORDINATOR_ADDR64, 0xFFFF);

// Optional LEDs
int statusLed = 11;
int errorLed = 12;
int pumpLed = 13;

float pirValue = 69.69;
String pumpState = "OFF";
unsigned long lastEventMs = 0;

String readPirSensor_cb(void *ctx) {
  pirValue += 0.1;
  if (pirValue > 100.0) pirValue = 69.69;
  char buf[12];
  dtostrf(pirValue, 0, 2, buf);
  return String(buf);
}

String readPumpState_cb(void *ctx) {
  return pumpState;
}

void pumpCommand_cb(const String &value, void *ctx) {
  Serial.print(F("[DeviceMain] pumpCommand_cb: "));
  Serial.println(value);
  if (value == "ON") {
    digitalWrite(13, HIGH);
    pumpState = "ON";
  } else if (value == "OFF") {
    digitalWrite(13, LOW);
    pumpState = "OFF";
  }
}

void flashLed(int pin, int times, int waitMs) {
  for (int i = 0; i < times; ++i) {
    digitalWrite(pin, HIGH);
    delay(waitMs);
    digitalWrite(pin, LOW);
    if (i + 1 < times) delay(waitMs);
  }
}

void setup() {
  pinMode(statusLed, OUTPUT);
  pinMode(errorLed, OUTPUT);
  pinMode(pumpLed, OUTPUT);
  digitalWrite(statusLed, LOW);
  digitalWrite(errorLed, LOW);
  digitalWrite(pumpLed, LOW);

  Serial.begin(9600);
  while (!Serial) { ; }
  Serial.println();
  Serial.println(F("[DeviceMain] Serial 9600"));

  xbeeSerial.begin(9600);
  delay(50);
  Serial.println(F("[DeviceMain] XBee AltSoftSerial started on pins RX=8 TX=9 at 9600"));

  bridge.begin(9600);

  bridge.addPublisher("PirSensor", "F", readPirSensor_cb, nullptr); // F = float
  bridge.addSubscriber("WaterPump", "S", readPumpState_cb, nullptr, pumpCommand_cb, nullptr); // S = string

  bridge.setManifestIntervalMs(15000);

  Serial.println(F("[DeviceMain] sending initial manifest (compact)"));
  bool ok = bridge.sendManifest();
  Serial.print(F("[DeviceMain] sendManifest returned: "));
  Serial.println(ok ? F("true") : F("false"));

  flashLed(statusLed, 1, 80);
  delay(200);
}

void loop() {
  bridge.loop();

  unsigned long now = millis();
  if (now - lastEventMs > 5000) {
    String val = readPirSensor_cb(nullptr);
    Serial.print(F("[DeviceMain] sending event (compact): "));
    Serial.println(val);
    bool ok = bridge.sendEvent("PirSensor", val.c_str());
    Serial.print(F("[DeviceMain] sendEvent returned: "));
    Serial.println(ok ? F("true") : F("false"));
    lastEventMs = now;
    if (ok) flashLed(statusLed, 1, 60);
    else flashLed(errorLed, 2, 80);
    delay(120);
  }

  delay(10);
}
