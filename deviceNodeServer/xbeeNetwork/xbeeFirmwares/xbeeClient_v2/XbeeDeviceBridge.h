#ifndef XBEE_DEVICE_BRIDGE_H
#define XBEE_DEVICE_BRIDGE_H

/*
  XbeeDeviceBridge.h
  AVR/UNO friendly public header.
  - No STL, no <vector>/<map>/<functional>.
  - Public API uses plain C types only (uint64_t, uint16_t).
  - Implementation converts these to XBee types inside the .cpp.
  - Requires ArduinoJson v6.
*/

#include <Arduino.h>
#include <ArduinoJson.h>
#include <stdint.h>

#define MAX_DEVICES 10 /* Limit this for low memory Atmega268 */
#define MAX_NAME_LEN 20
#define MAX_TYPE_LEN 12
#define MAX_VALUE_LEN 30

struct DeviceDescriptor {
  char Name[MAX_NAME_LEN];
  char Mode[12]; // "PUBLISHER" or "SUBSCRIBER"
  char Type[MAX_TYPE_LEN];
  char Value[MAX_VALUE_LEN];
};

// Value callback: return current value as String
typedef String (*ValueCallback)(void *ctx);
// Command callback: called with value string
typedef void (*CommandCallback)(const String &value, void *ctx);

// Transport abstraction (plain C types for addresses).
// addr64 is 64-bit address encoded as uint64_t (0 means none).
// addr16 is 16-bit address encoded as uint16_t (0xFFFF or 0 means none).
class Transport {
public:
  virtual ~Transport() {}
  virtual void begin(unsigned long baud) = 0;
  virtual bool send(const uint8_t *buf, size_t len, uint64_t addr64, uint16_t addr16) = 0;
  virtual void poll() = 0;
  typedef void (*ReceiveCb)(const String &payload, uint64_t addr64, uint16_t addr16, void *ctx);
  virtual void setReceiveCallback(ReceiveCb cb, void *ctx) = 0;
};

// Concrete transport declaration (implemented in .cpp).
// Constructor accepts XBee& and HardwareSerial& in the .cpp implementation.
class XBeeTransport : public Transport {
public:
  // Implementation defined in .cpp
  XBeeTransport(void *xbeePtr, HardwareSerial *serialPtr, unsigned long serialBaud = 9600);
  void begin(unsigned long baud) override;
  bool send(const uint8_t *buf, size_t len, uint64_t addr64, uint16_t addr16) override;
  void poll() override;
  void setReceiveCallback(ReceiveCb cb, void *ctx) override;

private:
  // Opaque pointers to avoid exposing XBee types in header
  void *_xbee_ptr;
  HardwareSerial *_serial_ptr;
  unsigned long _baud;
  ReceiveCb _cb;
  void *_cb_ctx;
};

// Main bridge class (no STL)
class XbeeDeviceBridge {
public:
  XbeeDeviceBridge(Transport *transport, const char *nodeName = nullptr, const char *macAddr = nullptr);

  void begin(unsigned long baud = 9600);
  void loop();

  bool addPublisher(const char *name, const char *type, ValueCallback cb, void *cb_ctx = nullptr);
  bool addSubscriber(const char *name, const char *type, ValueCallback valueCb, void *value_ctx, CommandCallback cmdCb, void *cmd_ctx);

  bool sendManifest();
  bool sendEvent(const char *deviceName, const char *value);

  void setManifestIntervalMs(unsigned long ms) { _manifestInterval = ms; }
  void setCommandAckEnabled(bool en) { _commandAck = en; }

  void setMessagePrefix(const char *p) { _prefix = String(p ? p : ""); }
  void setMessageSuffix(const char *s) { _suffix = String(s ? s : ""); }

private:
  Transport *_transport;

  DeviceDescriptor _devices[MAX_DEVICES];
  uint8_t _device_count;

  ValueCallback _publisherValueCbs[MAX_DEVICES];
  void* _publisherValueCtx[MAX_DEVICES];

  CommandCallback _subscriberCmdCbs[MAX_DEVICES];
  void* _subscriberCmdCtx[MAX_DEVICES];

  ValueCallback _subscriberValueCbs[MAX_DEVICES];
  void* _subscriberValueCtx[MAX_DEVICES];

  unsigned long _lastManifestMs;
  unsigned long _manifestInterval;
  bool _commandAck;
  String _prefix;
  String _suffix;

  void _onPayloadReceived(const String &payload, uint64_t addr64, uint16_t addr16);
  static void _transportTrampoline(const String &payload, uint64_t addr64, uint16_t addr16, void *ctx);

  void _processCommandJson(const JsonVariant &root);
  String _buildManifestJson();
  String _buildEventJson(const char *deviceName, const char *value);

  bool _sendPayload(const String &payload, uint64_t addr64 = 0, uint16_t addr16 = 0);

  int _find_device_index(const char *name);
  void _safe_strncpy(char *dst, const char *src, size_t maxlen);
};

#endif // XBEE_DEVICE_BRIDGE_H
