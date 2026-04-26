#ifndef XBEE_DEVICE_BRIDGE_H
#define XBEE_DEVICE_BRIDGE_H

#include <Arduino.h>

#define MAX_DEVICES 6
#define MAX_NAME_LEN 16
#define MAX_TYPE_LEN 8
#define MAX_VALUE_LEN 32

typedef String (*ValueCallback)(void *ctx);
typedef void (*CommandCallback)(const String &value, void *ctx);

struct DeviceDescriptor {
  char Name[MAX_NAME_LEN];
  char Mode[8];   // "PUBLISHER" or "SUBSCRIBER" (short)
  char Type[MAX_TYPE_LEN];
  char Value[MAX_VALUE_LEN];
};

class Transport {
public:
  virtual ~Transport() {}
  virtual void begin(unsigned long baud) = 0;
  virtual bool send(const uint8_t *buf, size_t len, uint64_t addr64, uint16_t addr16) = 0;
  virtual void poll() = 0;
  typedef void (*ReceiveCb)(const String &payload, uint64_t addr64, uint16_t addr16, void *ctx);
  virtual void setReceiveCallback(ReceiveCb cb, void *ctx) = 0;
};

class XBeeTransport : public Transport {
public:
  XBeeTransport(void *xbeePtr, Stream *serialPtr, unsigned long serialBaud = 9600);
  void begin(unsigned long baud) override;
  bool send(const uint8_t *buf, size_t len, uint64_t addr64, uint16_t addr16) override;
  void poll() override;
  void setReceiveCallback(ReceiveCb cb, void *ctx) override;

private:
  void *_xbee_ptr;
  Stream *_serial_ptr;
  unsigned long _baud;
  ReceiveCb _cb;
  void *_cb_ctx;
};

class XbeeDeviceBridge {
public:
  XbeeDeviceBridge(Transport *transport, uint64_t coordinatorAddr64 = 0ULL, uint16_t coordinatorAddr16 = 0xFFFF);

  void begin(unsigned long baud = 9600);
  void loop();

  bool addPublisher(const char *name, const char *type, ValueCallback cb, void *cb_ctx = nullptr);
  bool addSubscriber(const char *name, const char *type, ValueCallback valueCb, void *value_ctx, CommandCallback cmdCb, void *cmd_ctx);

  // Compact protocol: M/E/C frames ending with '#'
  bool sendManifest();               // sends one M:...# frame containing all devices
  bool sendEvent(const char *deviceName, const char *value); // sends E:...# frame

  void setManifestIntervalMs(unsigned long ms) { _manifestInterval = ms; }
  void setCommandAckEnabled(bool en) { _commandAck = en; }

  void setCoordinatorAddress(uint64_t addr64, uint16_t addr16 = 0xFFFF) { _coordinatorAddr64 = addr64; _coordinatorAddr16 = addr16; }

  static uint64_t parseHex64(const char *hex);

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

  uint64_t _coordinatorAddr64;
  uint16_t _coordinatorAddr16;

  void _onPayloadReceived(const String &payload, uint64_t addr64, uint16_t addr16);
  static void _transportTrampoline(const String &payload, uint64_t addr64, uint16_t addr16, void *ctx);

  void _processCommandString(const String &s);

  bool _sendPayload(const char *payloadBuf, size_t payloadLen, uint64_t addr64 = 0ULL, uint16_t addr16 = 0xFFFF);

  int _find_device_index(const char *name);
  void _safe_strncpy(char *dst, const char *src, size_t maxlen);
};

#endif // XBEE_DEVICE_BRIDGE_H
