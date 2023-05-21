//#include <Arduino_JSON.h>

//MQTT Node Firmware for esp 32
//
//
//OTA Headers
#include <ESPmDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
//
#include <ArduinoJson.h>
#include "DHT.h"
#include "EmonLib.h"
#include <driver/adc.h>
#include <LiquidCrystal.h>

#include <WiFi.h>
#include <PubSubClient.h>

//#include <Arduino_FreeRTOS.h>

#define DHTPIN 15     // Digital pin connected to the DHT sensor
#define ADC_INPUT 13
#define HOME_VOLTAGE 127.0
#define ADC_BITS    10
#define ADC_COUNTS  (1<<ADC_BITS)
#define DHTTYPE DHT11   // DHT 11

const char* ssid = "";
const char* password = "";
const char* mqtt_server = "";

LiquidCrystal My_LCD(14, 27, 26, 25, 33, 32);
DHT dht(DHTPIN, DHTTYPE);
EnergyMonitor emon1;
WiFiClient espClient;
PubSubClient client(espClient);

char out[600];
size_t cntBuff = 0;

char S_out[600];
size_t S_cntBuff = 0;

StaticJsonDocument<600> manifest;


String messageTemp;
float h;
float t;
float f;

double amps;
double watt;

void setup()
{
  Serial.begin(9600);
  
  adc2_config_channel_atten(ADC2_CHANNEL_4, ADC_ATTEN_DB_11);
  analogReadResolution(10);
  
  My_LCD.begin(16, 2);
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
  emon1.current(ADC_INPUT, 30);
    dht.begin();
    delay(2000);
    xTaskCreate(
    TaskLCDDisplay
    ,  "LCDDisplay"    // Nombre de la tarea
    ,  2600       // Tamaño de la pila de la tarea
    ,  NULL
    ,  1          // Prioridad, siendo 0 la de menor prioridad, y 3 la de mayor
    ,  NULL );

    xTaskCreate(
    TaskSensorRead
    ,  "SensorRead"    // Nombre de la tarea
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

void CreateManifest()
{
  manifest["Name"] = "MenyNode1";
  manifest["RootName"] = "/MenyNode1/";
JsonArray Devices = manifest.createNestedArray("Devices");

Devices.add("Temp");
Devices.add("Humidity");
Devices.add("Irms");
Devices.add("Pow");
Devices.add("LCDMsg");

cntBuff =serializeJson(manifest, out);
}

void setup_wifi() {
  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  My_LCD.clear();
  My_LCD.setCursor(0, 0);
  My_LCD.print("Connecting ...");
  
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  
  My_LCD.clear();
  My_LCD.setCursor(0, 0);
  My_LCD.print("Connected!");
  My_LCD.setCursor(0, 1);
  My_LCD.print(WiFi.localIP());
}

void callback(char* topic, byte* message, unsigned int length) {

  if (String(topic) == "/MenyNode1/LCDMsg/print") 
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
    Serial.println();
    //pending
  }
}

void reconnect() 
{
  // Loop until we're reconnected
  while (!client.connected()) 
  {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect("MenySensorNode1_MechLab")) 
    {
      Serial.println("connected");
      // Subscribe
      client.subscribe("/MenyNode1/LCDMsg/print");
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



void TaskLCDDisplay(void *pvParameters)
{
  (void) pvParameters;
  //pinMode(LED_BUILTIN, OUTPUT);
  while(true)
  {
    My_LCD.clear();
    My_LCD.setCursor(0, 0);
    My_LCD.print("Connected!");
    My_LCD.setCursor(0, 1);
    My_LCD.print(WiFi.localIP());
    delay(3000);

    My_LCD.clear();
    My_LCD.setCursor(0, 0);
    My_LCD.print(messageTemp);
    //vTaskDelay( 500 / portTICK_PERIOD_MS );
    delay(3000);

    My_LCD.clear();
    My_LCD.setCursor(0, 0);
    My_LCD.print("T: ");
    My_LCD.print(t);
    My_LCD.setCursor(0, 1);
    My_LCD.print("H: ");
    My_LCD.print(h);
    delay(3000);

    My_LCD.clear();
    My_LCD.setCursor(0, 0);
    My_LCD.print("Irms: ");
    My_LCD.print(amps);
    My_LCD.setCursor(0, 1);
    My_LCD.print("W: ");
    My_LCD.print(watt);
    delay(3000);
  }
  vTaskDelete( NULL );
}

void TaskSensorRead(void *pvParameters)
{
  (void) pvParameters;
  //pinMode(LED_BUILTIN, OUTPUT);
  while(true)
  {
  // Reading temperature or humidity takes about 250 milliseconds!
  // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
  h = dht.readHumidity();
  // Read temperature as Celsius (the default)
  t = dht.readTemperature();
  // Read temperature as Fahrenheit (isFahrenheit = true)
  f = dht.readTemperature(true);

  // Check if any reads failed and exit early (to try again).
  if (isnan(h) || isnan(t) || isnan(f)) {
    Serial.println(F("Failed to read from DHT sensor!"));
    delay(1000);
    //return;
    continue;
  }

  // Compute heat index in Fahrenheit (the default)
  float hif = dht.computeHeatIndex(f, h);
  // Compute heat index in Celsius (isFahreheit = false)
  float hic = dht.computeHeatIndex(t, h, false);

  Serial.print(F("Humidity: "));
  Serial.print(h);
  Serial.print(F("%  Temperature: "));
  Serial.print(t);
  Serial.print(F("°C "));
  Serial.print(f);
  Serial.print(F("°F  Heat index: "));
  Serial.print(hic);
  Serial.print(F("°C "));
  Serial.print(hif);
  Serial.println(F("°F"));


  amps = emon1.calcIrms(1480);
  watt = amps * HOME_VOLTAGE;

  Serial.print("Irms: ");
  Serial.print(amps);
  Serial.print("Watts: ");
  Serial.println(watt);

  StaticJsonDocument<200> Device1;
  Device1["Name"] = "Temperature";
  Device1["Mode"] = "PUBLISHER";
  Device1["Type"] = "FLOAT";
  Device1["Channel"] = "/MenyNode1/Temp";
  Device1["Value"] = "NOTHING";
  S_cntBuff =serializeJson(Device1, S_out);
  client.publish("/MenyNode1/Temp", S_out,S_cntBuff);

  Device1["Name"] = "Humidity";
  Device1["Mode"] = "PUBLISHER";
  Device1["Type"] = "FLOAT";
  Device1["Channel"] = "/MenyNode1/Humidity";
  Device1["Value"] = String(h,2);
  S_cntBuff =serializeJson(Device1, S_out);
  client.publish("/MenyNode1/Humidity", S_out,S_cntBuff);

  Device1["Name"] = "Irms";
  Device1["Mode"] = "PUBLISHER";
  Device1["Type"] = "FLOAT";
  Device1["Channel"] = "/MenyNode1/Irms";
  Device1["Value"] = String(amps,2);
  S_cntBuff =serializeJson(Device1, S_out);
  client.publish("/MenyNode1/Irms", S_out,S_cntBuff);

  Device1["Name"] = "Power";
  Device1["Mode"] = "PUBLISHER";
  Device1["Type"] = "FLOAT";
  Device1["Channel"] = "/MenyNode1/Pow";
  Device1["Value"] = String(watt,2);
  S_cntBuff =serializeJson(Device1, S_out);
  client.publish("/MenyNode1/Pow", S_out,S_cntBuff);

  Device1["Name"] = "LCDMsg";
  Device1["Mode"] = "SUBSCRIBER";
  Device1["Type"] = "STRING";
  Device1["Channel"] = "/MenyNode1/LCDMsg/print";
  Device1["Value"] = messageTemp;
  S_cntBuff =serializeJson(Device1, S_out);
  client.publish("/MenyNode1/LCDMsg", S_out,S_cntBuff);
  
  delay(3000);
  }
  vTaskDelete( NULL );
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
    
    client.publish("/MenyNode1/manifest", out, cntBuff );//
    delay(3000);
  }
  vTaskDelete( NULL );
}

void loop()
{
  ArduinoOTA.handle(); 
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  delay(500);
}
