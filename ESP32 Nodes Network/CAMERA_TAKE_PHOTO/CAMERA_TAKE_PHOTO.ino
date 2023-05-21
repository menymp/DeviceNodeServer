/*********
  cam photo socket server for device node server menymp
*********/
//OTA Headers
#include <ESPmDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>

#include <WiFi.h>
#include "esp_camera.h"
#include "esp_timer.h"
#include "img_converters.h"
#include "Arduino.h"


#include <PubSubClient.h>
#include <ArduinoJson.h>

#define CAMERA_MODEL_AI_THINKER

const char* mqtt_server = "";

// Replace with your network credentials
const char* ssid = "";
const char* password = "";

// OV2640 camera module pins (CAMERA_MODEL_AI_THINKER)
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


WiFiServer wifiServer(8072);
WiFiClient cliente;

WiFiClient espClient;
PubSubClient client(espClient);

char out[600];
size_t cntBuff = 0;

char S_out[600];
size_t S_cntBuff = 0;

StaticJsonDocument<600> manifest;

void setup() {
  // Serial port for debugging purposes
  Serial.begin(115200);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }

  // Print ESP32 Local IP Address
  Serial.print("IP Address: http://");
  Serial.println(WiFi.localIP());

ArduinoOTA
    .onStart([]() {
      String type;
      if (ArduinoOTA.getCommand() == U_FLASH)
        type = "sketch";
      else // U_SPIFFS
        type = "filesystem";

      // NOTE: if updating SPIFFS this would be the place to unmount SPIFFS using SPIFFS.end()
      Serial.println("Start updating " + type);
    })
    .onEnd([]() {
      Serial.println("\nEnd");
    })
    .onProgress([](unsigned int progress, unsigned int total) {
      Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
    })
    .onError([](ota_error_t error) {
      Serial.printf("Error[%u]: ", error);
      if (error == OTA_AUTH_ERROR) Serial.println("Auth Failed");
      else if (error == OTA_BEGIN_ERROR) Serial.println("Begin Failed");
      else if (error == OTA_CONNECT_ERROR) Serial.println("Connect Failed");
      else if (error == OTA_RECEIVE_ERROR) Serial.println("Receive Failed");
      else if (error == OTA_END_ERROR) Serial.println("End Failed");
    });

  ArduinoOTA.begin();

  // Turn-off the 'brownout detector'
  //WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

  // OV2640 camera module
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
  
  if (psramFound()) {
    //config.frame_size = FRAMESIZE_UXGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    //config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  #if defined(CAMERA_MODEL_ESP_EYE)
    pinMode(13, INPUT_PULLUP);
    pinMode(14, INPUT_PULLUP);
  #endif
  // Camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    ESP.restart();
  }
  
  wifiServer.begin();
  CreateManifest();
  client.setServer(mqtt_server, 1883);

  xTaskCreate(
    TaskPublishData
    ,  "LCDDisplay"    // Nombre de la tarea
    ,  2600       // Tamaño de la pila de la tarea
    ,  NULL
    ,  1          // Prioridad, siendo 0 la de menor prioridad, y 3 la de mayor
    ,  NULL );
}

void loop() {
  cliente = wifiServer.available();
 
  if (cliente) 
  {
    while (cliente.connected()) 
    {
      while (cliente.available()>0) 
      {
        char c = cliente.read();
        
        //processReceivedValue(c);
        if(c == 'k')
        {
          //Serial.println("Command Received");
          capturePhotoSaveSpiffs();
          //Serial.println("Photo sent");
          cliente.stop();
        }
        
      }
    }
    cliente.stop();
    //Serial.println("Client disconnected");
  }
}

String IpAddress2String(const IPAddress& ipAddress)
{
  return String(ipAddress[0]) + String(".") +\
  String(ipAddress[1]) + String(".") +\
  String(ipAddress[2]) + String(".") +\
  String(ipAddress[3])  ; 
}

void CreateManifest()
{
  manifest["Name"] = "MenyEspCam1";
  manifest["RootName"] = "/MenyEspCam1/";
JsonArray Devices = manifest.createNestedArray("Devices");

Devices.add("cam");

cntBuff =serializeJson(manifest, out);
}

void TaskPublishData(void *pvParameters)
{
  (void) pvParameters;
  //pinMode(LED_BUILTIN, OUTPUT);
  while(true)
  {
    Serial.println();
    Serial.print("num:");
    Serial.println(cntBuff);
    Serial.print(out);

    if (!client.connected()) {
      reconnect();
    }
    ArduinoOTA.handle(); 
    client.loop();
    delay(500);
    
    client.publish("/MenyEspCam1/manifest", out, cntBuff );//

    StaticJsonDocument<200> Device1;
    Device1["Name"] = "MenyEspCam1";
    Device1["Mode"] = "PUBLISHER";
    Device1["Type"] = "CAMERA";
    //Device1["Channel"] = String(WiFi.localIP())+":8072";
    Device1["Channel"] = IpAddress2String(WiFi.localIP())+":8072";
    Device1["Value"] = "jpg,k";
    S_cntBuff =serializeJson(Device1, S_out);
    
    client.publish("/MenyEspCam1/cam", S_out,S_cntBuff);
    client.loop();
    delay(3000);
  }
  vTaskDelete( NULL );
}

// Capture Photo and Save it to SPIFFS
void capturePhotoSaveSpiffs( void ) {
  camera_fb_t * fb = NULL; // pointer
  bool ok = 0; // Boolean indicating if the picture has been taken correctly

  fb = esp_camera_fb_get();
  if (!fb) 
  {
      Serial.println("Camera capture failed");
      return;
  }
  else 
  {
      cliente.write(fb->buf, fb->len); // payload (image), payload length
  }
  esp_camera_fb_return(fb);
}

void reconnect() 
{
  // Loop until we're reconnected
  while (!client.connected()) 
  {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect("MenyCamNode1_MechLab")) 
    {
      Serial.println("connected");
      // Subscribe
    } 
    else 
    {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}
