/*
  Simple XBee transmit example with verbose debug logging (SoftwareSerial)
  - Sends a fixed ASCII string to a remote 64-bit address.
  - Uses SoftwareSerial on pins 2 (RX) and 3 (TX).
  - Main Serial (USB) used for debug output.
  - Prints TX and RX frames, TX status, and hex/ascii payloads.
  - Assumes Series 1 XBee and Andrew Rapp XBee-Arduino library.
*/

#include <XBee.h>
#include <SoftwareSerial.h>
#include <AltSoftSerial.h>

// SoftwareSerial pins: RX, TX (Arduino pins)
static const uint8_t XBEE_SOFT_RX = 2; // connect XBee TX -> Arduino pin 2
static const uint8_t XBEE_SOFT_TX = 3; // connect XBee RX -> Arduino pin 3

// Global SoftwareSerial so XBee::setSerial gets a valid reference
//SoftwareSerial xbeeSerial(XBEE_SOFT_RX, XBEE_SOFT_TX);

AltSoftSerial xbeeSerial; // RX=8, TX=9

// XBee object
XBee xbee;

// Remote 64-bit address (SH, SL) — replace with your coordinator address
XBeeAddress64 remoteAddr64 = XBeeAddress64(0x..., 0x...);

// Timing
unsigned long lastSendMs = 0;
const unsigned long SEND_INTERVAL_MS = 5000; // send every 5 seconds

// TX status response holder
TxStatusResponse txStatus;

// LED pins (optional)
int statusLed = 11;
int errorLed = 12;

// Helper: flash LED
void flashLed(int pin, int times, int waitMs) {
  for (int i = 0; i < times; ++i) {
    digitalWrite(pin, HIGH);
    delay(waitMs);
    digitalWrite(pin, LOW);
    if (i + 1 < times) delay(waitMs);
  }
}

// Helper: print buffer as hex
void printHexBuffer(const uint8_t *buf, size_t len) {
  for (size_t i = 0; i < len; ++i) {
    if (buf[i] < 0x10) Serial.print('0');
    Serial.print(buf[i], HEX);
    if (i + 1 < len) Serial.print(' ');
  }
}

// Helper: print 64-bit address as hex string
void printAddr64(uint32_t msb, uint32_t lsb) {
  char tmp[32];
  sprintf(tmp, "%08lX%08lX", (unsigned long)msb, (unsigned long)lsb);
  Serial.print(tmp);
}

void setup() {
  pinMode(statusLed, OUTPUT);
  pinMode(errorLed, OUTPUT);
  digitalWrite(statusLed, LOW);
  digitalWrite(errorLed, LOW);

  // Debug serial (USB)
  Serial.begin(9600);
  while (!Serial) { ; }
  Serial.println();
  Serial.println(F("[Setup] Serial started at 115200"));

  // Start SoftwareSerial for XBee
  xbeeSerial.begin(9600);
  delay(50);
  Serial.println(F("[Setup] XBee SoftwareSerial started on pins RX=2 TX=3 at 9600"));

  // Attach SoftwareSerial to XBee object
  xbee.setSerial(xbeeSerial);
  Serial.println(F("[Setup] XBee serial attached"));

  Serial.print(F("[Setup] Remote 64-bit address: "));
  printAddr64(remoteAddr64.getMsb(), remoteAddr64.getLsb());
  Serial.println();

  Serial.println(F("[Setup] Ready to send fixed string every 5s"));
}

void loop() {
  unsigned long now = millis();

  // Send a simple fixed string at interval
  if (lastSendMs == 0 || (now - lastSendMs >= SEND_INTERVAL_MS)) {
    const char *msg = "Hello from device";
    size_t len = strlen(msg);

    // Build a Tx64Request with a copy of the payload (safe lifetime)
    // The XBee library does not guarantee copying, so construct with a local buffer object.
    uint8_t buf[64];
    if (len > sizeof(buf)) len = sizeof(buf);
    memcpy(buf, msg, len);

    Tx64Request tx(remoteAddr64, buf, (uint8_t)len);

    Serial.print(F("[TX] Sending to "));
    printAddr64(remoteAddr64.getMsb(), remoteAddr64.getLsb());
    Serial.print(F("  payload (ascii): "));
    Serial.println(msg);
    Serial.print(F("[TX] payload (hex): "));
    printHexBuffer(buf, len);
    Serial.println();

    xbee.send(tx);
    lastSendMs = now;

    flashLed(statusLed, 1, 80);
  }

  // Poll for incoming frames and TX status for a short window
  // Use a small readPacket timeout so SoftwareSerial can capture frames
  if (xbee.readPacket(200)) {
    uint8_t apiId = xbee.getResponse().getApiId();
    Serial.print(F("[RX] Frame received. API ID: 0x"));
    if (apiId < 0x10) Serial.print('0');
    Serial.println(apiId, HEX);

    if (apiId == RX_16_RESPONSE) {
      Rx16Response rx16;
      xbee.getResponse().getRx16Response(rx16);
      int len = rx16.getDataLength();
      Serial.print(F("[RX16] From 16-bit: 0x"));
      Serial.print(rx16.getRemoteAddress16(), HEX);
      Serial.print(F("  RSSI: "));
      Serial.print(rx16.getRssi(), DEC);
      Serial.print(F("  Len: "));
      Serial.println(len);
      if (len > 0) {
        Serial.print(F("[RX16] Payload (hex): "));
        for (int i = 0; i < len; ++i) {
          if (rx16.getData(i) < 0x10) Serial.print('0');
          Serial.print(rx16.getData(i), HEX);
          if (i + 1 < len) Serial.print(' ');
        }
        Serial.println();
        Serial.print(F("[RX16] Payload (ascii): "));
        for (int i = 0; i < len; ++i) {
          char c = (char)rx16.getData(i);
          Serial.print(isPrintable(c) ? c : '.');
        }
        Serial.println();
      }
    } else if (apiId == RX_64_RESPONSE) {
      Rx64Response rx64;
      xbee.getResponse().getRx64Response(rx64);
      int len = rx64.getDataLength();
      XBeeAddress64 src = rx64.getRemoteAddress64();
      uint32_t msb = src.getMsb();
      uint32_t lsb = src.getLsb();
      Serial.print(F("[RX64] From 64-bit: "));
      printAddr64(msb, lsb);
      Serial.print(F("  RSSI: "));
      Serial.print(rx64.getRssi(), DEC);
      Serial.print(F("  Len: "));
      Serial.println(len);
      if (len > 0) {
        Serial.print(F("[RX64] Payload (hex): "));
        for (int i = 0; i < len; ++i) {
          if (rx64.getData(i) < 0x10) Serial.print('0');
          Serial.print(rx64.getData(i), HEX);
          if (i + 1 < len) Serial.print(' ');
        }
        Serial.println();
        Serial.print(F("[RX64] Payload (ascii): "));
        for (int i = 0; i < len; ++i) {
          char c = (char)rx64.getData(i);
          Serial.print(isPrintable(c) ? c : '.');
        }
        Serial.println();
      }
    } else if (apiId == TX_STATUS_RESPONSE) {
      xbee.getResponse().getTxStatusResponse(txStatus);
      Serial.print(F("[TX_STATUS] FrameId: "));
      Serial.print(txStatus.getFrameId(), DEC);
      Serial.print(F("  Status: 0x"));
      if (txStatus.getStatus() < 0x10) Serial.print('0');
      Serial.println(txStatus.getStatus(), HEX);
      if (txStatus.getStatus() == SUCCESS) {
        Serial.println(F("[TX_STATUS] Delivery SUCCESS"));
        flashLed(statusLed, 2, 60);
      } else {
        Serial.println(F("[TX_STATUS] Delivery FAILED or NO ACK"));
        flashLed(errorLed, 3, 200);
      }
    } else {
      Serial.print(F("[RX] Unhandled API ID: 0x"));
      Serial.println(apiId, HEX);
    }
  } else {
    if (xbee.getResponse().isError()) {
      Serial.print(F("[Error] readPacket error code: "));
      Serial.println(xbee.getResponse().getErrorCode(), HEX);
    }
    // no frame available this cycle
  }

  // small delay to avoid tight loop
  delay(50);
}
