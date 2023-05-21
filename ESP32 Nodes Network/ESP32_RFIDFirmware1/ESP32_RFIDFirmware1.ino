/*
 * ESP32 Firmware demo for RFID sensor integration
 * https://www.hackster.io/270906/mqtt-based-event-management-using-esp8266-and-rfid-678c54
 */
//OTA Headers
#include <ESPmDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
//communication libraries
#include <ArduinoJson.h>
#include <WiFi.h>
#include <PubSubClient.h>

#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN  5  // ESP32 pin GIOP5 
#define RST_PIN 27 // ESP32 pin GIOP27 

#define LOCK_PIN 13

const char* ssid = "";
const char* password = "";
const char* mqtt_server = "";

MFRC522 rfid(SS_PIN, RST_PIN);

WiFiClient espClient;
PubSubClient client(espClient);

char out[600];
size_t cntBuff = 0;

char S_out[600];
size_t S_cntBuff = 0;

StaticJsonDocument<600> manifest;

byte readCard[4];
int lockState = 1;
String messageTemp;

void setup() {
  Serial.begin(9600);
  SPI.begin(); // init SPI bus
  rfid.PCD_Init(); // init MFRC522

  Serial.println("Tap an RFID/NFC tag on the RFID-RC522 reader");
  //adc2_config_channel_atten(ADC2_CHANNEL_4, ADC_ATTEN_DB_11);
  //analogReadResolution(10);

  pinMode(LOCK_PIN,OUTPUT); //check for availability pin
  digitalWrite(LOCK_PIN, LOW); 
  
  CreateManifest();
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
  
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

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
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  delay(500);
}

void CreateManifest()
{
  manifest["Name"] = "MenyNodeRF1";
  manifest["RootName"] = "/MenyNodeRF1/";
  JsonArray Devices = manifest.createNestedArray("Devices");

  Devices.add("Rfid");
  Devices.add("Lock");

  cntBuff =serializeJson(manifest, out);
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

void callback(char* topic, byte* message, unsigned int length) {

  if (String(topic) == "/MenyNodeRF1/Lock/open") 
  {
    Serial.print("Message arrived on topic: ");
    Serial.print(topic);
    Serial.print(". Message: ");
    messageTemp = "";
    for (int i = 0; i < length; i++) 
    {
      Serial.print((char)message[i]);
      messageTemp += (char)message[i];
    }
    if(messageTemp == "OPEN")
    {
      lockState = 0;
      digitalWrite(LOCK_PIN, HIGH); 
      delay(3000);
      digitalWrite(LOCK_PIN, LOW); 
      lockState = 1;
    }
  }
}

void reconnect() 
{
  // Loop until we're reconnected
  while (!client.connected()) 
  {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect("MenyNodeRF1")) 
    {
      Serial.println("connected");
      // Subscribe
      client.subscribe("/MenyNodeRF1/Lock/open");
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

void TaskRfidRead(void *pvParameters)
{
  (void) pvParameters;
  int cnt = 0;
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

        //Expect to add a buffer as a signal in the future
        //digitalWrite(buzzer,HIGH);
        //delay(500);
        //digitalWrite(buzzer,LOW);
        
        for (int i = 0; i < rfid.uid.size; i++) 
        {  
          readCard[i] = rfid.uid.uidByte[i];   
          Serial.print(readCard[i], HEX);  
        }
        char msg[50];
        msg[0]='\0';
        array_to_string(readCard,4,msg);
        //byte mac[6];
        //WiFi.macAddress(mac);
        //char msg1[50];
        //msg1[0]='\0';
        //array_to_string(mac,6,msg1);
        //char mid[]=",";
        char finalMsg[50];
        finalMsg[0]='\0';
        strcat(finalMsg,msg);
        //strcat(finalMsg,mid);
        //strcat(finalMsg,msg1);
        Serial.print("final msg:");
        Serial.println(finalMsg);
        //Serial.print("MAC: ");
        //Serial.println(WiFi.macAddress());
        //client.publish(pubtopic2,finalMsg);
   
        StaticJsonDocument<200> Device1;
        Device1["Name"] = "Rfid";
        Device1["Mode"] = "PUBLISHER";
        Device1["Type"] = "STRING";
        Device1["Channel"] = "/MenyNodeRF1/Rfid";
        Device1["Value"] = finalMsg;
        S_cntBuff =serializeJson(Device1, S_out);
        client.publish("/MenyNodeRF1/Rfid", S_out,S_cntBuff);

        rfid.PICC_HaltA(); // halt PICC
        rfid.PCD_StopCrypto1(); // stop encryption on PCD
      }
    }
    if(cnt == 15)
    {
        StaticJsonDocument<200> Device1;
        Device1["Name"] = "Lock";
        Device1["Mode"] = "SUBSCRIBER";
        Device1["Type"] = "STRING";
        Device1["Channel"] = "/MenyNodeRF1/Lock/open";
        Device1["Value"] = String(lockState,2);
        S_cntBuff =serializeJson(Device1, S_out);
        client.publish("/MenyNodeRF1/Rfid", S_out,S_cntBuff);
    }
    cnt++;
    delay(200);
  }
  vTaskDelete( NULL );
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
    
    client.publish("/MenyNodeRF1/manifest", out, cntBuff );//
    delay(3000);
  }
  vTaskDelete( NULL );
}
