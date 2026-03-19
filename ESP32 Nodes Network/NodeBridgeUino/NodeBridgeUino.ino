#include <WiFi.h>
#include "node_bridge.h"

#define WIFI_SSID ""
#define WIFI_PASS ""
#define MQTT_BROKER ""
#define MQTT_PORT 1883

// Mock callbacks
String mockTemp() { return String(25.5, 1); }
String mockCounter() { return String(42); }
void pumpHandler(const String &payload) { Serial.println("Pump command: " + payload); }

NodeBridge *bridge;

int i = 0;

void setup() {
  Serial.begin(9600);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) delay(200);
  Serial.println("WiFi connected: " + WiFi.localIP().toString());

  bridge = new NodeBridge("ESP32Node", MQTT_BROKER, MQTT_PORT);
  bridge->begin();

  // Wait a bit for ack from server, or poll ackEvent in production
  delay(1000);

  // Add mock devices (if ack required, ensure ackEvent true before adding)
  bridge->addPublisher("TempSensor", "FLOAT", mockTemp);
  bridge->addPublisher("Counter", "INT", mockCounter);
  bridge->addSubscriber("PumpMotor", "STRING", []()->String { return String("OFF"); }, pumpHandler);
}

void loop() {
  bridge->loop();
  delay(10);
  if (i > 1000)
  {
    bridge->sendEvent("TempSensor", "69.69");
    i = 0;
  }
  i++;
}
