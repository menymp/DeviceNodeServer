#ifndef NODE_BRIDGE_H
#define NODE_BRIDGE_H

#include <Arduino.h>
#include <WiFi.h>            // use <ESP8266WiFi.h> on ESP8266
#include <PubSubClient.h>
#include <ArduinoJson.h>

#define NODEBRIDGE_MAX_DEVICES 16

typedef String (*ValueCallback)();
typedef void (*CommandCallback)(const String &payload);

struct Device {
  String Name;
  String Mode; // "PUBLISHER" or "SUBSCRIBER"
  String Type;
  String Channel;
  ValueCallback value_callback;
  CommandCallback command_callback;
};

class NodeBridge {
public:
  NodeBridge(const String &nodeName, const String &mqttBroker, uint16_t mqttPort = 1883);

  // Network and MQTT lifecycle
  void begin();                       // initialize WiFi (if needed) and MQTT client
  void loop();                        // call frequently from main loop
  void disable();                     // graceful stop

  // Registration
  void acknowledge();                 // connect and register immediately (optional)

  // Device management
  bool addPublisher(const String &name, const String &type, ValueCallback cb);
  bool addSubscriber(const String &name, const String &type, ValueCallback cb, CommandCallback cmd);
  void removeDevice(const String &name);
  bool deviceExists(const String &name);
  bool sendEvent(const String &name, const String & value);
  bool getDevice(const String &name, Device * device);

  // Configuration helpers
  void setSamplingTimeSeconds(unsigned long s); // default 6
  void setKeepaliveSeconds(unsigned long k);    // default 60

private:
  // configuration
  String Name;
  String RootPath;
  String mqttBroker;
  uint16_t mqttPort;
  unsigned long keepaliveSeconds;
  unsigned long samplingTimeSeconds;

  // runtime
  Device devices[NODEBRIDGE_MAX_DEVICES];
  int deviceCount;
  String ipAddr;
  String macAddr;
  String ackPath;
  std::vector<String> validTypes; // optional, filled from server

  // flags and timers
  bool ackEvent;
  bool errorEvent;
  bool reconnectEvent;
  bool stopEvent;
  unsigned long lastPayloadMs;
  unsigned long samplingTimeMs;
  unsigned long timeoutAckMs;

  // networking
  WiFiClient wifiClient;
  PubSubClient mqttClient;

  // internal helpers
  void initClient();
  void registerNode();
  void buildAndSendManifest();
  void resubscribeDevices();
  void safeSubscribe(const String &topic);
  void safePublish(const String &topic, const String &payload);
  void tryReconnect(int maxAttempts = 5);
  void checkAckTimeout();
  Device* getSubscriberByTopic(const String &topic);
  bool validateDeviceArgs(const String &name, const String &type, ValueCallback cb);

  // MQTT callback
  void onMqttMessage(char* topic, byte* payload, unsigned int length);
  static void mqttCallbackRouter(char* topic, byte* payload, unsigned int length, void* user);
};

#endif // NODE_BRIDGE_H
