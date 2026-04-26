#include "XbeeDeviceBridge.h"
#include <XBee.h>

#define TMP_SZ 128
#define SEND_TIMEOUT_MS 300

// ---------------- XBeeTransport ----------------

XBeeTransport::XBeeTransport(void *xbeePtr, Stream *serialPtr, unsigned long serialBaud)
  : _xbee_ptr(xbeePtr), _serial_ptr(serialPtr), _baud(serialBaud), _cb(nullptr), _cb_ctx(nullptr)
{
}

void XBeeTransport::begin(unsigned long baud) {
  _baud = baud;
  if (_xbee_ptr && _serial_ptr) {
    XBee *xbee = static_cast<XBee*>(_xbee_ptr);
    xbee->setSerial(*_serial_ptr);
  }
  delay(20);
}

// Send using API frames but wait for TX_STATUS (timeout) to avoid overlapping frames.
bool XBeeTransport::send(const uint8_t *buf, size_t len, uint64_t addr64, uint16_t addr16) {
  XBee *xbee = static_cast<XBee*>(_xbee_ptr);
  if (!xbee) return false;
  if (!buf || len == 0) return false;

  // limit copy size
  size_t use = len;
  if (use > TMP_SZ) use = TMP_SZ;

  // debug hex dump (minimal)
  Serial.print(F("[XBeeTransport] send len="));
  Serial.println(len);

  // prepare local copy
  uint8_t tmp[TMP_SZ];
  memcpy(tmp, buf, use);

  // send appropriate frame
  if (addr64 != 0ULL) {
    uint32_t high = (uint32_t)(addr64 >> 32);
    uint32_t low  = (uint32_t)(addr64 & 0xFFFFFFFFUL);
    XBeeAddress64 addr64obj(high, low);
    Tx64Request tx(addr64obj, tmp, (uint8_t)use);
    xbee->send(tx);
  } else if (addr16 != 0 && addr16 != 0xFFFF) {
    Tx16Request tx16(addr16, tmp, (uint8_t)use);
    xbee->send(tx16);
  } else {
    Tx16Request tx16_bcast(0xFFFE, tmp, (uint8_t)use);
    xbee->send(tx16_bcast);
  }

  // wait for TX_STATUS
  uint32_t start = millis();
  while (millis() - start < SEND_TIMEOUT_MS) {
    xbee->readPacket(50);
    if (xbee->getResponse().isAvailable()) {
      uint8_t apiId = xbee->getResponse().getApiId();
      if (apiId == TX_STATUS_RESPONSE) {
        TxStatusResponse txStatus;
        xbee->getResponse().getTxStatusResponse(txStatus);
        Serial.print(F("[XBeeTransport] TX_STATUS 0x"));
        Serial.println(txStatus.getStatus(), HEX);
        return (txStatus.getStatus() == SUCCESS);
      }
      // ignore other frames here
    }
  }
  // timed out
  Serial.println(F("[XBeeTransport] TX_STATUS timeout"));
  return false;
}

void XBeeTransport::setReceiveCallback(ReceiveCb cb, void *ctx) {
  _cb = cb;
  _cb_ctx = ctx;
}

void XBeeTransport::poll() {
  XBee *xbee = static_cast<XBee*>(_xbee_ptr);
  if (!xbee) return;

  xbee->readPacket(50);

  if (xbee->getResponse().isAvailable()) {
    uint8_t apiId = xbee->getResponse().getApiId();

    if (apiId == RX_16_RESPONSE) {
      Rx16Response rx16;
      xbee->getResponse().getRx16Response(rx16);
      int len = rx16.getDataLength();
      if (len > 0 && _cb) {
        String payload;
        for (int i = 0; i < len; ++i) payload += (char)rx16.getData(i);
        _cb(payload, 0ULL, rx16.getRemoteAddress16(), _cb_ctx);
      }
    } else if (apiId == RX_64_RESPONSE) {
      Rx64Response rx64;
      xbee->getResponse().getRx64Response(rx64);
      int len = rx64.getDataLength();
      if (len > 0 && _cb) {
        String payload;
        for (int i = 0; i < len; ++i) payload += (char)rx64.getData(i);
        XBeeAddress64 a64 = rx64.getRemoteAddress64();
        uint64_t addr64 = ((uint64_t)a64.getMsb() << 32) | (uint64_t)a64.getLsb();
        _cb(payload, addr64, 0xFFFF, _cb_ctx);
      }
    } else if (apiId == TX_STATUS_RESPONSE) {
      // handled in send() loop; ignore here
    }
  }
}

// ---------------- XbeeDeviceBridge ----------------

uint64_t XbeeDeviceBridge::parseHex64(const char *hex) {
  uint64_t value = 0;
  if (!hex) return 0;
  if (hex[0] == '0' && (hex[1] == 'x' || hex[1] == 'X')) hex += 2;
  for (const char *p = hex; *p; ++p) {
    char c = *p;
    uint8_t nib;
    if (c >= '0' && c <= '9') nib = c - '0';
    else if (c >= 'A' && c <= 'F') nib = 10 + (c - 'A');
    else if (c >= 'a' && c <= 'f') nib = 10 + (c - 'a');
    else break;
    value = (value << 4) | (uint64_t)nib;
  }
  return value;
}

XbeeDeviceBridge::XbeeDeviceBridge(Transport *transport, uint64_t coordinatorAddr64, uint16_t coordinatorAddr16)
  : _transport(transport),
    _device_count(0),
    _lastManifestMs(0),
    _manifestInterval(60000),
    _commandAck(true),
    _coordinatorAddr64(coordinatorAddr64),
    _coordinatorAddr16(coordinatorAddr16)
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
  if (_transport) _transport->setReceiveCallback(XbeeDeviceBridge::_transportTrampoline, this);
}

void XbeeDeviceBridge::begin(unsigned long baud) {
  if (_transport) _transport->begin(baud);
  _lastManifestMs = millis();
  Serial.println(F("[XbeeDeviceBridge] begin"));
  if (_coordinatorAddr64 != 0ULL) {
    Serial.print(F("[XbeeDeviceBridge] configured coordinator: "));
    char buf[32];
    sprintf(buf, "%08lX%08lX", (unsigned long)(_coordinatorAddr64 >> 32), (unsigned long)(_coordinatorAddr64 & 0xFFFFFFFFUL));
    Serial.println(buf);
  } else {
    Serial.println(F("[XbeeDeviceBridge] no coordinator configured; using broadcast"));
  }
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
  _safe_strncpy(_devices[idx].Mode, "P", sizeof(_devices[idx].Mode)); // P = publisher
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
  _safe_strncpy(_devices[idx].Mode, "S", sizeof(_devices[idx].Mode)); // S = subscriber
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

// Build a compact manifest string: M<count>:Name,Mode,Type,Value;...#
bool XbeeDeviceBridge::sendManifest() {
  if (_device_count == 0) return false;

  char buf[TMP_SZ];
  size_t pos = 0;

  // header M<count>:
  int n = snprintf(buf + pos, sizeof(buf) - pos, "M%d:", _device_count);
  if (n < 0) return false;
  pos += (size_t)n;
  if (pos >= sizeof(buf) - 4) return false;

  for (int i = 0; i < _device_count; ++i) {
    String valStr = "";
    if (_publisherValueCbs[i]) valStr = _publisherValueCbs[i](_publisherValueCbs[i] ? _publisherValueCtx[i] : nullptr);
    else valStr = String(_devices[i].Value);
    if (valStr.length() == 0) valStr = String("");

    // encode: Name,Mode,Type,Value
    n = snprintf(buf + pos, sizeof(buf) - pos, "%s,%s,%s,%s", _devices[i].Name, _devices[i].Mode, _devices[i].Type, valStr.c_str());
    if (n < 0) return false;
    pos += (size_t)n;
    if (i + 1 < _device_count) {
      if (pos < sizeof(buf) - 2) {
        buf[pos++] = ';';
        buf[pos] = '\0';
      } else return false;
    }
    if (pos >= sizeof(buf) - 4) break;
  }

  // terminator
  if (pos < sizeof(buf) - 2) {
    buf[pos++] = '#';
    buf[pos] = '\0';
  } else return false;

  Serial.print(F("[XbeeDeviceBridge] sendManifest -> "));
  Serial.println(buf);

  // ensure payload small enough
  if (pos > TMP_SZ) return false;

  return _sendPayload(buf, pos, _coordinatorAddr64, _coordinatorAddr16);
}

// Build event: E:Name,Mode,Type,Value#
bool XbeeDeviceBridge::sendEvent(const char *deviceName, const char *value) {
  if (!deviceName) return false;
  char buf[TMP_SZ];
  int n = snprintf(buf, sizeof(buf), "E:%s,%s,%s,%s#", deviceName, "P", "F", value ? value : "");
  if (n <= 0) return false;
  size_t len = (size_t)n;
  Serial.print(F("[XbeeDeviceBridge] sendEvent -> "));
  Serial.println(buf);
  return _sendPayload(buf, len, _coordinatorAddr64, _coordinatorAddr16);
}

void XbeeDeviceBridge::_transportTrampoline(const String &payload, uint64_t addr64, uint16_t addr16, void *ctx) {
  if (!ctx) return;
  XbeeDeviceBridge *self = static_cast<XbeeDeviceBridge*>(ctx);
  self->_onPayloadReceived(payload, addr64, addr16);
}

void XbeeDeviceBridge::_onPayloadReceived(const String &payload, uint64_t addr64, uint16_t addr16) {
  Serial.print(F("[XbeeDeviceBridge] RX from "));
  if (addr64 != 0ULL) {
    char buf[32];
    sprintf(buf, "%08lX%08lX", (unsigned long)(addr64 >> 32), (unsigned long)(addr64 & 0xFFFFFFFFUL));
    Serial.print(buf);
  } else {
    Serial.print(F("16:"));
    Serial.print(addr16, HEX);
  }
  Serial.print(F(" -> "));
  Serial.println(payload);

  // Expect frames ending with '#'
  if (!payload.endsWith("#")) {
    Serial.println(F("[XbeeDeviceBridge] frame missing terminator '#', ignoring"));
    return;
  }

  // Trim trailing '#'
  String s = payload.substring(0, payload.length() - 1);

  // If command frame C:Device,Value
  if (s.startsWith("C:")) {
    _processCommandString(s);
    return;
  }

  // If other frames (E/M) could be handled here if needed
  // For this device we only process incoming commands (C:)
}

void XbeeDeviceBridge::_processCommandString(const String &s) {
  // s = "C:Device,Value" or "C:Device" (value optional)
  int colon = s.indexOf(':');
  if (colon < 0) return;
  String body = s.substring(colon + 1);
  int comma = body.indexOf(',');
  String dev = (comma >= 0) ? body.substring(0, comma) : body;
  String val = (comma >= 0) ? body.substring(comma + 1) : String("");

  dev.trim();
  val.trim();

  int idx = _find_device_index(dev.c_str());
  if (idx >= 0 && _subscriberCmdCbs[idx]) {
    _subscriberCmdCbs[idx](val, _subscriberCmdCtx[idx]);
    if (_commandAck) {
      char ack[TMP_SZ];
      int n = snprintf(ack, sizeof(ack), "A:%s,OK#", dev.c_str());
      if (n > 0) _sendPayload(ack, (size_t)n);
    }
  } else {
    if (_commandAck) {
      char nack[TMP_SZ];
      int n = snprintf(nack, sizeof(nack), "A:%s,UNKNOWN#", dev.c_str());
      if (n > 0) _sendPayload(nack, (size_t)n);
    }
  }
}

bool XbeeDeviceBridge::_sendPayload(const char *payloadBuf, size_t payloadLen, uint64_t addr64, uint16_t addr16) {
  if (!_transport) return false;
  if (!payloadBuf || payloadLen == 0) return false;

  uint64_t dest64 = addr64;
  uint16_t dest16 = addr16;
  if (dest64 == 0ULL && (dest16 == 0 || dest16 == 0xFFFF)) {
    if (_coordinatorAddr64 != 0ULL) {
      dest64 = _coordinatorAddr64;
      dest16 = _coordinatorAddr16;
    } else {
      dest16 = 0xFFFE; // broadcast
    }
  }

  bool ok = _transport->send((const uint8_t *)payloadBuf, payloadLen, dest64, dest16);
  if (ok) {
    Serial.print(F("[XbeeDeviceBridge] payload queued (len="));
    Serial.print(payloadLen);
    Serial.print(F(") dest64="));
    if (dest64 != 0ULL) {
      char tmp[32];
      sprintf(tmp, "%08lX%08lX", (unsigned long)(dest64 >> 32), (unsigned long)(dest64 & 0xFFFFFFFFUL));
      Serial.print(tmp);
    } else {
      Serial.print(F("none"));
    }
    Serial.print(F(" dest16="));
    Serial.println(dest16, HEX);
  } else {
    Serial.println(F("[XbeeDeviceBridge] transport->send returned false"));
  }
  return ok;
}
