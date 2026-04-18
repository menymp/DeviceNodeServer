/*
 * ESP32 Firmware demo for RFID sensor integration
 * https://www.hackster.io/270906/mqtt-based-event-management-using-esp8266-and-rfid-678c54
 */
//OTA Headers
#include <ESPmDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
#include <WiFi.h>
#include "node_bridge.h"

#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN  5  // ESP32 pin GIOP5 
#define RST_PIN 27 // ESP32 pin GIOP27 

#define LOCK_PIN 13

const char* ssid = "";
const char* password = "";
const char* MQTT_BROKER = "";
const int MQTT_PORT = 1883;

MFRC522 rfid(SS_PIN, RST_PIN);

WiFiClient espClient;
PubSubClient client(espClient);
NodeBridge *bridge;

char last_rfid_id[50] = {0};  /* last scanned rfid */

byte readCard[4];
int lockState = 0;

void setup() {
  Serial.begin(9600);
  SPI.begin(); // init SPI bus
  rfid.PCD_Init(); // init MFRC522

  Serial.println("Tap an RFID/NFC tag on the RFID-RC522 reader");

  pinMode(LOCK_PIN,OUTPUT); //check for availability pin
  digitalWrite(LOCK_PIN, LOW); 
  setup_wifi();

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

  delay(2000);

  xTaskCreate(
    TaskRfidRead
    ,  "TaskRfidRead"    // Nombre de la tarea
    ,  2600       // Tamaño de la pila de la tarea
    ,  NULL
    ,  2          // Prioridad, siendo 0 la de menor prioridad, y 3 la de mayor
    ,  NULL );
    
  xTaskCreate(
    TaskPublishData
    ,  "PublishData"    // Nombre de la tarea
    ,  2600       // Tamaño de la pila de la tarea
    ,  NULL
    ,  2          // Prioridad, siendo 0 la de menor prioridad, y 3 la de mayor
    ,  NULL );
}

void loop() {
  ArduinoOTA.handle(); 
  delay(500);
}

String read_last_scan()
{
   return String(last_rfid_id);
}

String read_lock_state()
{
   return String(lockState);
}

void lock_command_callback(const String &payload)
{
  Serial.println("Lock command received: " + payload);
  if(payload == "OPEN")
  {
      lockState = 1;
      digitalWrite(LOCK_PIN, HIGH); 
      delay(3000);
      digitalWrite(LOCK_PIN, LOW); 
      lockState = 0;
  }
  else
  {
      digitalWrite(LOCK_PIN, LOW); 
      lockState = 0;
  }
}

void array_to_string(byte a[],unsigned int len,char buffer[])
{
  for(unsigned int i=0;i<len;i++)
  {
    byte nib1=(a[i]>>4)&0x0F;
    byte nib2=(a[i]>>0)&0x0F;
    buffer[i*2+0]=nib1 < 0x0A ? '0' + nib1 : 'A'+ nib1 - 0x0A;
    buffer[i*2+1]=nib2 < 0x0A ? '0' + nib2 : 'A'+ nib2 - 0x0A;
  }
  buffer[len*2]='\0';
}

void init_device_node()
{
  bridge = new NodeBridge("MenyNodeRF1", MQTT_BROKER, MQTT_PORT);
  bridge->begin();
  
  // Wait a bit for ack from server, or poll ackEvent in production
  delay(2000);
  bridge->addPublisher("Rfid", "STRING", read_last_scan);
  bridge->addSubscriber("Lock", "STRING", read_lock_state, lock_command_callback);
  Serial.println("Node init");
}

void setup_wifi() {
  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void TaskRfidRead(void *pvParameters)
{
  (void) pvParameters;
  while(true)
  {
    
    if (rfid.PICC_IsNewCardPresent()) 
    { // new tag is available
      if (rfid.PICC_ReadCardSerial()) 
      { // NUID has been readed
        MFRC522::PICC_Type piccType = rfid.PICC_GetType(rfid.uid.sak);
        Serial.print("RFID/NFC Tag Type: ");
        Serial.println(rfid.PICC_GetTypeName(piccType));

        // print UID in Serial Monitor in the hex format
        Serial.print("UID:");
        for (int i = 0; i < rfid.uid.size; i++) 
        {  
          readCard[i] = rfid.uid.uidByte[i];   
          Serial.print(readCard[i], HEX);  
        }
        char msg[50];
        msg[0]='\0';
        array_to_string(readCard,4,msg);
        last_rfid_id[0] = '\0';
        strcat(last_rfid_id,msg);
        Serial.print("New Scanned Id:");
        Serial.println(last_rfid_id);
        bridge->sendEvent("Rfid", read_last_scan());

        rfid.PICC_HaltA(); // halt PICC
        rfid.PCD_StopCrypto1(); // stop encryption on PCD
      }
    }
    delay(200);
  }
  vTaskDelete( NULL );
}

void TaskPublishData(void *pvParameters)
{
  (void) pvParameters;
   init_device_node();
 
  while(true)
  {
    bridge->loop();
    delay(10);
  }
  vTaskDelete( NULL );
}
