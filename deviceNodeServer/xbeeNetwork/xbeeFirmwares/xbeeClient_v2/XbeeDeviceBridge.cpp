/*
  XbeeDeviceBridge.cpp
  Implementation that uses Andrew Rapp xbee-arduino (XBee.h).
  - No STL.
  - Public header uses only uint64_t/uint16_t for addresses.
  - This .cpp converts those to XBee types internally.
  - Requires ArduinoJson v6.
*/

#include "XbeeDeviceBridge.h"
#include <XBee.h> // Andrew Rapp xbee-arduino
// Note: XBee.h provides Tx16Request, Tx64Request, Rx16Response, Rx64Response, XBeeAddress64, etc.

// -------------------- XBeeTransport implementation --------------------

XBeeTransport::XBeeTransport(void *xbeePtr, HardwareSerial *serialPtr, unsigned long serialBaud)
  : _xbee_ptr(xbeePtr), _serial_ptr(serialPtr), _baud(serialBaud), _cb(nullptr), _cb_ctx(nullptr)
{
}

void XBeeTransport::begin(unsigned long baud) {
  _baud = baud;
  if (_serial_ptr) _serial_ptr->begin(_baud);
  // set serial on XBee object if provided
  if (_xbee_ptr && _serial_ptr) {
    XBee *xbee = static_cast<XBee*>(_xbee_ptr);
    xbee->setSerial(*_serial_ptr);
  }
  delay(50);
}

bool XBeeTransport::send(const uint8_t *buf, size_t len, uint64_t addr64, uint16_t addr16) {
  XBee *xbee = static_cast<XBee*>(_xbee_ptr);
  if (!xbee) return false;

  // If addr64 provided (non-zero), send Tx64Request
  if (addr64 != 0) {
    uint32_t high = (uint32_t)(addr64 >> 32);
    uint32_t low  = (uint32_t)(addr64 & 0xFFFFFFFFUL);
    XBeeAddress64 addr64obj(high, low);
    Tx64Request tx64(addr64obj, const_cast<uint8_t*>(buf), (uint8_t)len);
    xbee->send(tx64);
    return true;
  }

  // If 16-bit address provided (non-zero and not 0xFFFF), send Tx16Request using numeric address
  if (addr16 != 0 && addr16 != 0xFFFF) {
    // Andrew Rapp's library supports Tx16Request(uint16_t, uint8_t*, uint8_t)
    Tx16Request tx16(addr16, const_cast<uint8_t*>(buf), (uint8_t)len);
    xbee->send(tx16);
    return true;
  }

  // Fallback: broadcast 16-bit 0xFFFE
  Tx16Request tx16_bcast(0xFFFE, const_cast<uint8_t*>(buf), (uint8_t)len);
  xbee->send(tx16_bcast);
  return true;
}

void XBeeTransport::setReceiveCallback(ReceiveCb cb, void *ctx) {
  _cb = cb;
  _cb_ctx = ctx;
}

void XBeeTransport::poll() {
  XBee *xbee = static_cast<XBee*>(_xbee_ptr);
  if (!xbee) return;

  // readPacket with short timeout to be responsive
  xbee->readPacket(10);

  if (xbee->getResponse().isAvailable()) {
    uint8_t apiId = xbee->getResponse().getApiId();

    if (apiId == RX_16_RESPONSE) {
      Rx16Response rx16;
      xbee->getResponse().getRx16Response(rx16);
      int len = rx16.getDataLength();
      if (len > 0) {
        String payload;
        for (int i = 0; i < len; ++i) payload += (char)rx16.getData(i);
        if (_cb) {
          // rx16.getRemoteAddress16() returns a 16-bit address (library supports this)
          uint16_t remote16 = rx16.getRemoteAddress16();
          _cb(payload, 0ULL, remote16, _cb_ctx);
        }
      }
    } else if (apiId == RX_64_RESPONSE) {
      Rx64Response rx64;
      xbee->getResponse().getRx64Response(rx64);
      int len = rx64.getDataLength();
      if (len > 0) {
        String payload;
        for (int i = 0; i < len; ++i) payload += (char)rx64.getData(i);
        if (_cb) {
          XBeeAddress64 a64 = rx64.getRemoteAddress64();
          uint64_t addr64 = ((uint64_t)a64.getMsb() << 32) | (uint64_t)a64.getLsb();
          _cb(payload, addr64, 0xFFFF, _cb_ctx);
        }
      }
    } else {
      // ignore other frames
    }
  }
}

// -------------------- XbeeDeviceBridge implementation --------------------

XbeeDeviceBridge::XbeeDeviceBridge(Transport *transport, const char *nodeName, const char *macAddr)
  : _transport(transport),
    _device_count(0),
    _lastManifestMs(0),
    _manifestInterval(60000),
    _commandAck(true),
    _prefix(""),
    _suffix("")
{
  for (int i = 0; i < MAX_DEVICES; ++i) {
    _publisherValueCbs[i] = nullptr;
    _publisherValueCtx[i] = nullptr;
    _subscriberCmdCbs[i] = nullptr;
    _subscriberCmdCtx[i] = nullptr;
    _subscriberValueCbs[i] = nullptr;
    _subscriberValueCtx[i] = nullptr;
    _devices[i].Name[0] = '\0';
    _devices[i].Mode[0] = '\0';
    _devices[i].Type[0] = '\0';
    _devices[i].Value[0] = '\0';
  }

  if (_transport) {
    _transport->setReceiveCallback(XbeeDeviceBridge::_transportTrampoline, this);
  }
}

void XbeeDeviceBridge::begin(unsigned long baud) {
  if (_transport) _transport->begin(baud);
  _lastManifestMs = millis();
}

void XbeeDeviceBridge::loop() {
  if (_transport) _transport->poll();
  unsigned long now = millis();
  if (_manifestInterval > 0 && (now - _lastManifestMs >= _manifestInterval)) {
    sendManifest();
    _lastManifestMs = now;
  }
}

void XbeeDeviceBridge::_safe_strncpy(char *dst, const char *src, size_t maxlen) {
  if (!src) { dst[0] = '\0'; return; }
  strncpy(dst, src, maxlen - 1);
  dst[maxlen - 1] = '\0';
}

int XbeeDeviceBridge::_find_device_index(const char *name) {
  if (!name) return -1;
  for (int i = 0; i < _device_count; ++i) {
    if (strncmp(_devices[i].Name, name, MAX_NAME_LEN) == 0) return i;
  }
  return -1;
}

bool XbeeDeviceBridge::addPublisher(const char *name, const char *type, ValueCallback cb, void *cb_ctx) {
  if (!name || !type || !cb) return false;
  if (_device_count >= MAX_DEVICES) return false;
  if (_find_device_index(name) >= 0) return false;

  int idx = _device_count++;
  _safe_strncpy(_devices[idx].Name, name, MAX_NAME_LEN);
  _safe_strncpy(_devices[idx].Mode, "PUBLISHER", sizeof(_devices[idx].Mode));
  _safe_strncpy(_devices[idx].Type, type, MAX_TYPE_LEN);
  _devices[idx].Value[0] = '\0';

  _publisherValueCbs[idx] = cb;
  _publisherValueCtx[idx] = cb_ctx;
  return true;
}

bool XbeeDeviceBridge::addSubscriber(const char *name, const char *type, ValueCallback valueCb, void *value_ctx, CommandCallback cmdCb, void *cmd_ctx) {
  if (!name || !type || !cmdCb) return false;
  if (_device_count >= MAX_DEVICES) return false;
  if (_find_device_index(name) >= 0) return false;

  int idx = _device_count++;
  _safe_strncpy(_devices[idx].Name, name, MAX_NAME_LEN);
  _safe_strncpy(_devices[idx].Mode, "SUBSCRIBER", sizeof(_devices[idx].Mode));
  _safe_strncpy(_devices[idx].Type, type, MAX_TYPE_LEN);
  _devices[idx].Value[0] = '\0';

  _subscriberCmdCbs[idx] = cmdCb;
  _subscriberCmdCtx[idx] = cmd_ctx;
  if (valueCb) {
    _subscriberValueCbs[idx] = valueCb;
    _subscriberValueCtx[idx] = value_ctx;
  } else {
    _subscriberValueCbs[idx] = nullptr;
    _subscriberValueCtx[idx] = nullptr;
  }
  return true;
}

String XbeeDeviceBridge::_buildManifestJson() {
  const size_t CAP = 750;
  StaticJsonDocument<CAP> doc;
  JsonArray arr = doc.createNestedArray("Devices");

  for (int i = 0; i < _device_count; ++i) {
    JsonObject obj = arr.createNestedObject();
    obj["Name"] = _devices[i].Name;
    obj["Mode"] = _devices[i].Mode;
    obj["Type"] = _devices[i].Type;
    if (strcmp(_devices[i].Mode, "PUBLISHER") == 0) {
      if (_publisherValueCbs[i]) {
        String v = _publisherValueCbs[i](_publisherValueCtx[i]);
        obj["Value"] = v;
      } else {
        obj["Value"] = _devices[i].Value;
      }
    } else {
      if (_subscriberValueCbs[i]) {
        String v = _subscriberValueCbs[i](_subscriberValueCtx[i]);
        obj["Value"] = v;
      } else {
        obj["Value"] = _devices[i].Value;
      }
    }
  }

  String out;
  serializeJson(doc, out);
  return out;
}

String XbeeDeviceBridge::_buildEventJson(const char *deviceName, const char *value) {
  const size_t CAP = 256;
  StaticJsonDocument<CAP> doc;
  JsonObject obj = doc.to<JsonObject>();
  obj["Name"] = deviceName;
  obj["Mode"] = "PUBLISHER";
  obj["Type"] = "STRING";
  obj["Value"] = value ? String(value) : String("");
  String out;
  serializeJson(doc, out);
  return out;
}

bool XbeeDeviceBridge::sendManifest() {
  String json = _buildManifestJson();
  if (json.length() == 0) return false;
  return _sendPayload(json);
}

bool XbeeDeviceBridge::sendEvent(const char *deviceName, const char *value) {
  if (!deviceName) return false;
  String json = _buildEventJson(deviceName, value ? value : "");
  return _sendPayload(json);
}

void XbeeDeviceBridge::_transportTrampoline(const String &payload, uint64_t addr64, uint16_t addr16, void *ctx) {
  if (!ctx) return;
  XbeeDeviceBridge *self = static_cast<XbeeDeviceBridge*>(ctx);
  self->_onPayloadReceived(payload, addr64, addr16);
}

void XbeeDeviceBridge::_onPayloadReceived(const String &payload, uint64_t addr64, uint16_t addr16) {
  const size_t CAP = 512;
  StaticJsonDocument<CAP> doc;
  DeserializationError err = deserializeJson(doc, payload);
  if (err) return;
  JsonVariant root = doc.as<JsonVariant>();
  if (root.is<JsonObject>() && root.containsKey("Device") && root.containsKey("Value")) {
    _processCommandJson(root);
  }
}

void XbeeDeviceBridge::_processCommandJson(const JsonVariant &root) {
  const char *dev = root["Device"];
  const char *val = root["Value"];
  if (!dev) return;
  String devName = String(dev);
  String value = val ? String(val) : String("");

  int idx = _find_device_index(devName.c_str());
  if (idx >= 0 && _subscriberCmdCbs[idx]) {
    _subscriberCmdCbs[idx](value, _subscriberCmdCtx[idx]);

    if (_commandAck) {
      const size_t CAP = 192;
      StaticJsonDocument<CAP> ack;
      ack["Device"] = devName;
      ack["Ack"] = "OK";
      ack["Value"] = value;
      String out;
      serializeJson(ack, out);
      _sendPayload(out);
    }
  } else {
    if (_commandAck) {
      const size_t CAP = 128;
      StaticJsonDocument<CAP> nack;
      nack["Device"] = devName;
      nack["Ack"] = "UNKNOWN";
      String out;
      serializeJson(nack, out);
      _sendPayload(out);
    }
  }
}

bool XbeeDeviceBridge::_sendPayload(const String &payload, uint64_t addr64, uint16_t addr16) {
  if (!_transport) return false;
  String out = _prefix + payload + _suffix;
  size_t len = out.length();
  return _transport->send((const uint8_t *)out.c_str(), len, addr64, addr16);
}
