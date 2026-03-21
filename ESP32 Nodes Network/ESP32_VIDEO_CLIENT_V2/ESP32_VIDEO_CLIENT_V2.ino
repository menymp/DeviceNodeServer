#include <WiFi.h>
#include "esp_camera.h"

// ---------- CONFIG ----------
const char* ssid = "";
const char* password = "";

const char* server_ip = ""; // ingest server IP
const uint16_t server_port = 9000;

const char* CAMERA_NAME = "MenyEspCam1";
const char CAMERA_TYPE = '1'; // single digit char '0'..'9'
const unsigned long CAPTURE_INTERVAL_MS = 1000; // 1 fps
// ----------------------------

WiFiClient client;

// Camera pins for AI Thinker (adjust if different module)
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

void setupCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_SVGA;
  config.jpeg_quality = 4;
  config.fb_count = 1;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Camera init failed");
    while (true) delay(1000);
  }
}

void connectWiFi() {
  WiFi.begin(ssid, password);
  WiFi.setSleep(WIFI_PS_NONE);
  Serial.print("Connecting to WiFi");
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
    Serial.print(".");
    if (millis() - start > 20000) {
      Serial.println("\nWiFi connect timeout, restarting...");
      ESP.restart();
    }
  }
  Serial.println("\nWiFi connected");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

bool connectServer() {
  if (client.connected()) return true;
  Serial.printf("Connecting to server %s:%u ...\n", server_ip, server_port);
  if (!client.connect(server_ip, server_port)) {
    Serial.println("Server connect failed");
    return false;
  }
  client.setNoDelay(true);
  Serial.println("Connected to server");
  return true;
}

void writeUint32BE(WiFiClient &c, uint32_t v) {
  uint8_t b[4];
  b[0] = (v >> 24) & 0xFF;
  b[1] = (v >> 16) & 0xFF;
  b[2] = (v >> 8) & 0xFF;
  b[3] = v & 0xFF;
  c.write(b, 4);
}

String getMac() {
  uint8_t mac[6];
  esp_read_mac(mac, ESP_MAC_WIFI_STA);
  char buf[18];
  sprintf(buf, "%02X%02X%02X%02X%02X%02X",
          mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  return String(buf);
}

void sendFrame() {
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }

  // Build JSON header (small, no external libs)
  // Example: {"name":"MenyEspCam1","camera_type":"1","mac":"AA:BB:CC:DD:EE:FF","frame_size":12345}
  String mac = getMac();
  char headerBuf[256];
  
  int headerLen = snprintf(headerBuf, sizeof(headerBuf),
                           "{\"name\":\"%s\",\"camera_type\":\"%c\",\"mac\":\"%s\",\"frame_size\":%u}",
                           CAMERA_NAME, CAMERA_TYPE, mac.c_str(), (unsigned)fb->len);
  if (headerLen <= 0 || headerLen >= (int)sizeof(headerBuf)) {
    Serial.println("Header build failed or too large");
    esp_camera_fb_return(fb);
    return;
  }

  // Send header length + header, then image length + image
  writeUint32BE(client, (uint32_t)headerLen);
  client.write((const uint8_t*)headerBuf, headerLen);

  writeUint32BE(client, (uint32_t)fb->len);
  // send image payload
  client.write(fb->buf, fb->len);
  client.flush();

  //Serial.printf("Sent header %d bytes and image %u bytes\n", headerLen, (unsigned)fb->len);

  esp_camera_fb_return(fb);
}

void setup() {
  Serial.begin(115200);
  connectWiFi();
  setupCamera();
}

void loop() {
  static unsigned long backoff = 1000;
  if (!connectServer()) {
    delay(backoff);
    backoff = min(backoff * 2, 10000UL);
    return;
  }
  backoff = 1000; // reset backoff on success

  // Optional: simple keepalive read to detect server close (non-blocking)
  if (client.available()) {
    // consume any server messages if you plan to use control channel
    while (client.available()) client.read();
  }

  sendFrame();

  // Sleep between captures
  //delay(CAPTURE_INTERVAL_MS);
}
