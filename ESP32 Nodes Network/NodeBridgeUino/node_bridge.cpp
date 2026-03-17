#include "node_bridge.h"

// If using ESP8266, include the correct header in your sketch before including NodeBridge
// #include <ESP8266WiFi.h>

NodeBridge::NodeBridge(const String &nodeName, const String &mqttBroker, uint16_t mqttPort)
  : Name(nodeName),
    RootPath("/" + nodeName + "/"),
    mqttBroker(mqttBroker),
    mqttPort(mqttPort),
    mqttClient(wifiClient),
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
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    char buf[18];
    sprintf(buf, "%02x:%02x:%02x:%02x:%02x:%02x",
            mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    macAddr = String(buf);
  } else {
    ipAddr = "";
    macAddr = "";
  }

  // configure mqtt client
  mqttClient.setServer(mqttBroker.c_str(), mqttPort);
  // set callback using lambda capturing this pointer
  mqttClient.setCallback([this](char* topic, byte* payload, unsigned int length){
    this->onMqttMessage(topic, payload, length);
  });
}

void NodeBridge::setSamplingTimeSeconds(unsigned long s) {
  samplingTimeSeconds = s;
  samplingTimeMs = s * 1000UL;
}

void NodeBridge::setKeepaliveSeconds(unsigned long k) {
  keepaliveSeconds = k;
}

void NodeBridge::begin() {
  // Ensure WiFi is active; user sketch should connect WiFi before calling begin
  if (WiFi.status() == WL_CONNECTED) {
    ipAddr = WiFi.localIP().toString();
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    char buf[18];
    sprintf(buf, "%02x:%02x:%02x:%02x:%02x:%02x",
            mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    macAddr = String(buf);
  }
  initClient();
  // attempt immediate connect and register
  acknowledge();
}

void NodeBridge::initClient() {
  // mqttClient already configured in constructor; nothing else required here
}

void NodeBridge::acknowledge() {
  if (!mqttClient.connected()) {
    if (!mqttClient.connect(Name.c_str())) {
      reconnectEvent = true;
      return;
    }
  }
  registerNode();
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

  if (!mqttClient.connected()) {
    if (reconnectEvent) tryReconnect();
    return;
  }

  // process incoming messages
  mqttClient.loop();

  // check ack timeout
  checkAckTimeout();

  // scheduled manifest
  if (ackEvent && !stopEvent) {
    unsigned long now = millis();
    if ((now - lastPayloadMs) >= samplingTimeMs) {
      buildAndSendManifest();
      lastPayloadMs = now;
    }
  }
}

void NodeBridge::tryReconnect(int maxAttempts) {
  for (int attempt = 1; attempt <= maxAttempts; ++attempt) {
    if (WiFi.status() != WL_CONNECTED) {
      delay(2000);
      continue;
    }
    if (mqttClient.connect(Name.c_str())) {
      registerNode();
      resubscribeDevices();
      reconnectEvent = false;
      lastPayloadMs = millis();
      return;
    } else {
      unsigned long backoff = min(5000UL + attempt * 2000UL, 30000UL);
      unsigned long jitter = random(0, 1000);
      delay(backoff + jitter);
    }
  }
  // leave reconnectEvent true so caller can retry later
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
  if (!mqttClient.subscribe(topic.c_str())) {
    // subscribe failed; will be retried on reconnect
  }
}

void NodeBridge::safePublish(const String &topic, const String &payload) {
  if (!mqttClient.connected()) return;
  mqttClient.publish(topic.c_str(), payload.c_str());
}

bool NodeBridge::addPublisher(const String &name, const String &type, ValueCallback cb) {
  if (deviceExists(name)) return false;
  if (!validateDeviceArgs(name, type, cb)) return false;
  if (deviceCount >= NODE_BRIDGE_MAX_DEVICES) return false;
  devices[deviceCount++] = {name, "PUBLISHER", type, RootPath + name + "/value", cb, nullptr};
  return true;
}

bool NodeBridge::addSubscriber(const String &name, const String &type, ValueCallback cb, CommandCallback cmd) {
  if (deviceExists(name)) return false;
  if (!validateDeviceArgs(name, type, cb)) return false;
  if (deviceCount >= NODE_BRIDGE_MAX_DEVICES) return false;
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
  if (!getDevice(&device))
  {
    return false;
  }
  if (devices[i].Mode == "SUBSCRIBER") 
  {
    return false;
  }

  DynamicJsonDocument devicePayload(1024);
  devicePayload["Name"] = devices.Name;
  devicePayload["Mode"] = devices.Mode;
  devicePayload["Type"] = devices.Type;
  devicePayload["Channel"] = devices.Channel;
  devicePayload["Value"] = value;


  String payload;
  serializeJson(devicePayload, payload);

  safePublish(devices.Channel, payload);
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

void NodeBridge::disable() {
  stopEvent = true;
  if (mqttClient.connected()) mqttClient.disconnect();
}
