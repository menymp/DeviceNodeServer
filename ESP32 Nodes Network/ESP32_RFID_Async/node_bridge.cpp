#include "node_bridge.h"

// If using ESP8266, include the correct header in your sketch before including NodeBridge
// #include <ESP8266WiFi.h>

NodeBridge::NodeBridge(const String &nodeName, const String &mqttBroker, uint16_t mqttPort)
  : Name(nodeName),
    RootPath("/" + nodeName + "/"),
    mqttBroker(mqttBroker),
    mqttPort(mqttPort),
    deviceCount(0),
    ackEvent(false),
    errorEvent(false),
    reconnectEvent(false),
    stopEvent(false),
    timeoutAckMs(6000)
{
  keepaliveSeconds = 60;
  samplingTimeSeconds = 6;
  samplingTimeMs = samplingTimeSeconds * 1000UL;
  lastPayloadMs = millis();

  // get IP and MAC if WiFi already connected; otherwise leave empty
  if (WiFi.status() == WL_CONNECTED) {
    ipAddr = WiFi.localIP().toString();
    macAddr = getMacNoDots();
  } else {
    ipAddr = "";
    macAddr = "";
  }

  // configure mqtt client server (AsyncMqttClient uses setServer)
  // configure mqtt client (Async)
  mqttClient.setServer(mqttBroker.c_str(), mqttPort);
  mqttClient.setClientId(Name.c_str());
  mqttClient.setCleanSession(true);

  // set callbacks
  mqttClient.onConnect([this](bool sessionPresent){ this->onAsyncMqttConnect(sessionPresent); });
  mqttClient.onDisconnect([this](AsyncMqttClientDisconnectReason reason){ this->onAsyncMqttDisconnect(reason); });
  mqttClient.onMessage([this](char* topic, char* payload, AsyncMqttClientMessageProperties properties, size_t len, size_t index, size_t total){
    this->onAsyncMqttMessage(topic, payload, properties, len, index, total);
  });
  Serial.println("NodeBridge constructed; MQTT callbacks set");

  // backoff init
  reconnectBackoffMs = 2000;
  lastReconnectAttemptMs = 0;
}

// returns MAC as 12 hex chars (e.g. "AABBCCDDEEFF")
String NodeBridge::getMacNoDots() {
  uint8_t mac[6];
  // Arduino WiFi provides this overload to fill raw bytes
  WiFi.macAddress(mac);
  char buf[13]; // 12 chars + null
  sprintf(buf, "%02X%02X%02X%02X%02X%02X",
          mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  return String(buf);
}

void NodeBridge::setSamplingTimeSeconds(unsigned long s) {
  samplingTimeSeconds = s;
  samplingTimeMs = s * 1000UL;
}

void NodeBridge::setKeepaliveSeconds(unsigned long k) {
  keepaliveSeconds = k;
}

void NodeBridge::begin() {
  if (WiFi.status() == WL_CONNECTED) {
    ipAddr = WiFi.localIP().toString();
    macAddr = getMacNoDots();
  }
  initClient();
  Serial.println("NodeBridge begin: calling mqttClient.connect()");
  if (WiFi.status() == WL_CONNECTED) {
    mqttClient.connect(); // non-blocking
  } else {
    reconnectEvent = true;
  }
}

void NodeBridge::acknowledge() {
  // start async connect; registration will be done in onAsyncMqttConnect
  if (!mqttClient.connected()) {
    mqttClient.connect();
    reconnectEvent = true;
    return;
  }
  // if already connected, register immediately
  registerNode();
}

void NodeBridge::initClient() {
  // Async client already configured in constructor
}

void NodeBridge::onAsyncMqttConnect(bool sessionPresent) {
  Serial.println("AsyncMqtt: connected");
  // register node and resubscribe only after connection
  registerNode();
  resubscribeDevices();
  reconnectEvent = false;
  lastPayloadMs = millis();
}

void NodeBridge::onAsyncMqttDisconnect(AsyncMqttClientDisconnectReason reason) {
  Serial.print("AsyncMqtt: disconnected reason=");
  Serial.println("AsyncMqtt: disconnected, scheduling reconnect");
  Serial.println((int)reason);
  reconnectEvent = true;
  lastReconnectAttemptMs = millis(); // record when we last attempted/observed disconnect
}

void NodeBridge::onAsyncMqttMessage(char* topic, char* payload, AsyncMqttClientMessageProperties properties, size_t len, size_t index, size_t total) {
  // Build a temporary byte buffer if your existing onMqttMessage expects byte*
  // Here we call your existing onMqttMessage which expects (char* topic, byte* payload, unsigned int length)
  onMqttMessage(topic, (byte*)payload, (unsigned int)len);
}


void NodeBridge::registerNode() {
  ackPath = ipAddr + "/" + Name + "/ack";
  DynamicJsonDocument doc(256);
  doc["Name"] = Name;
  doc["AcknowledgePath"] = ackPath;
  doc["MacAddress"] = macAddr;
  String payload;
  serializeJson(doc, payload);

  safeSubscribe(ackPath);
  safePublish("/node_name_request", payload);
  lastPayloadMs = millis();
}

void NodeBridge::loop() {
  if (stopEvent) return;

  if (WiFi.status() != WL_CONNECTED) {
    reconnectEvent = true;
    delay(500);
    return;
  }

  if (!mqttClient.connected()) {
    if (reconnectEvent) tryReconnect(0);
    delay(200);
    return;
  }

  // Async client handles I/O; still call checkAckTimeout and scheduled manifest
  checkAckTimeout();
  if (ackEvent && !stopEvent) {
    unsigned long now = millis();
    if ((now - lastPayloadMs) >= samplingTimeMs) {
      buildAndSendManifest();
      lastPayloadMs = now;
    }
  }
}

void NodeBridge::tryReconnect(int maxAttempts) {
  // Async connect is non-blocking; call connect() with backoff
  if (!reconnectEvent) return;
  if (WiFi.status() != WL_CONNECTED) return;

  unsigned long now = millis();
  if (now - lastReconnectAttemptMs < reconnectBackoffMs) return;

  Serial.println("tryReconnect: calling mqttClient.connect()");
  mqttClient.connect();
  lastReconnectAttemptMs = now;
  // exponential backoff up to 30s
  reconnectBackoffMs = min(reconnectBackoffMs * 2, 30000UL);
}

void NodeBridge::checkAckTimeout() {
  if (!ackEvent) {
    if ((millis() - lastPayloadMs) > timeoutAckMs) {
      reconnectEvent = true;
    }
  }
}

void NodeBridge::buildAndSendManifest() {
  // guard memory by sizing doc based on device count
  size_t base = 512 + deviceCount * 256;
  DynamicJsonDocument doc(base);
  doc["Name"] = Name;
  doc["RootName"] = RootPath;
  doc["ip"] = ipAddr;
  doc["mac_addr"] = macAddr;
  doc["acknowledge_path"] = ackPath;
  JsonArray arr = doc.createNestedArray("Devices");
  for (int i = 0; i < deviceCount; ++i) {
    JsonObject obj = arr.createNestedObject();
    obj["Name"] = devices[i].Name;
    obj["Mode"] = devices[i].Mode;
    obj["Type"] = devices[i].Type;
    obj["Channel"] = devices[i].Channel;
    String val = "";
    if (devices[i].value_callback) {
      val = devices[i].value_callback();
    }
    obj["Value"] = val;
  }
  String payload;
  serializeJson(doc, payload);
  safePublish("/inbound", payload);
}

void NodeBridge::safeSubscribe(const String &topic) {
  if (!mqttClient.connected()) return;
  mqttClient.subscribe(topic.c_str(), 0);
}

void NodeBridge::safePublish(const String &topic, const String &payload) {
  if (!mqttClient.connected()) {
    Serial.println("safePublish: mqtt not connected, dropping publish");
    return;
  }
  uint16_t packetId = mqttClient.publish(topic.c_str(), 0, false, payload.c_str());
  if (packetId == 0) {
    Serial.println("safePublish: publish returned 0 (failed)");
  }
}

bool NodeBridge::addPublisher(const String &name, const String &type, ValueCallback cb) {
  if (deviceExists(name)) return false;
  if (!validateDeviceArgs(name, type, cb)) return false;
  if (deviceCount >= NODEBRIDGE_MAX_DEVICES) return false;
  devices[deviceCount++] = {name, "PUBLISHER", type, RootPath + name + "/value", cb, nullptr};
  return true;
}

bool NodeBridge::addSubscriber(const String &name, const String &type, ValueCallback cb, CommandCallback cmd) {
  if (deviceExists(name)) return false;
  if (!validateDeviceArgs(name, type, cb)) return false;
  if (deviceCount >= NODEBRIDGE_MAX_DEVICES) return false;
  devices[deviceCount++] = {name, "SUBSCRIBER", type, RootPath + name + "/value", cb, cmd};
  safeSubscribe(RootPath + name + "/value");
  return true;
}

void NodeBridge::removeDevice(const String &name) {
  for (int i = 0; i < deviceCount; ++i) {
    if (devices[i].Name == name) {
      // shift left
      for (int j = i; j < deviceCount - 1; ++j) devices[j] = devices[j + 1];
      deviceCount--;
      break;
    }
  }
}

bool NodeBridge::deviceExists(const String &name) {
  for (int i = 0; i < deviceCount; ++i) if (devices[i].Name == name) return true;
  return false;
}

bool NodeBridge::getDevice(const String &name, Device * device) {
  for (int i = 0; i < deviceCount; ++i) if (devices[i].Name == name) 
  {
    *device = devices[i];
    return true;
  }
  return false;
}

bool NodeBridge::sendEvent(const String &name, const String & value) {
  Device device;
  if (!getDevice(name, &device))
  {
    return false;
  }
  if (device.Mode == "SUBSCRIBER") 
  {
    return false;
  }

  DynamicJsonDocument devicePayload(1024);
  devicePayload["Name"] = device.Name;
  devicePayload["Mode"] = device.Mode;
  devicePayload["Type"] = device.Type;
  devicePayload["Channel"] = device.Channel;
  devicePayload["Value"] = value;


  String payload;
  serializeJson(devicePayload, payload);

  safePublish(device.Channel, payload);
  return true;
}

bool NodeBridge::validateDeviceArgs(const String &name, const String &type, ValueCallback cb) {
  if (name.length() == 0) return false;
  if (cb == nullptr) return false;
  // if validTypes is populated, check membership (left as optional)
  return true;
}

Device* NodeBridge::getSubscriberByTopic(const String &topic) {
  for (int i = 0; i < deviceCount; ++i) {
    if (devices[i].Mode == "SUBSCRIBER" && devices[i].Channel == topic) return &devices[i];
  }
  return nullptr;
}

void NodeBridge::onMqttMessage(char* topic, byte* payload, unsigned int length) {
  String t = String(topic);
  String msg;
  for (unsigned int i = 0; i < length; ++i) msg += (char)payload[i];

  if (t == ackPath) {
    DynamicJsonDocument doc(512);
    DeserializationError err = deserializeJson(doc, msg);
    if (err) {
      errorEvent = true;
      return;
    }
    const char* result = doc["result"] | "";
    validTypes.clear();
    if (doc.containsKey("valid_types")) {
      for (JsonVariant v : doc["valid_types"].as<JsonArray>()) {
        validTypes.push_back(String((const char*)v));
      }
    }
    if (validTypes.size() == 0 || String(result) == "" || String(result) == "ERR_ACK") {
      errorEvent = true;
    } else if (String(result) == "SUCCESS_ACK") {
      ackEvent = true;
      reconnectEvent = false;
      timeoutEvent = false;
      updtEvent = true;
      resubscribeDevices();
      lastPayloadMs = millis();
    }
    return;
  }

  Device* d = getSubscriberByTopic(t);
  if (d && d->command_callback) {
    d->command_callback(msg);
  }
}

void NodeBridge::resubscribeDevices() {
   for (int i = 0; i < deviceCount; i++) {
    if (devices[i].Mode == "SUBSCRIBER") safeSubscribe(devices[i].Channel);
  }
}

void NodeBridge::disable() {
  stopEvent = true;
  if (mqttClient.connected()) mqttClient.disconnect();
}
