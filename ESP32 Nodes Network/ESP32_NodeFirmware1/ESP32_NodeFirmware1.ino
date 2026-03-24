//MQTT Node Firmware for esp 32
//
//
//OTA Headers
#include <ESPmDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
//
#include "DHT.h"
#include "EmonLib.h"
#include <driver/adc.h>
#include <LiquidCrystal.h>
#include "node_bridge.h"
#include <WiFi.h>

#define DHTPIN 15     // Digital pin connected to the DHT sensor
#define ADC_INPUT 13
#define HOME_VOLTAGE 127.0
#define ADC_BITS    10
#define ADC_COUNTS  (1<<ADC_BITS)
#define DHTTYPE DHT11   // DHT 11

const char* ssid = "";
const char* password = "";
const char* MQTT_BROKER = "";
const int MQTT_PORT = 1883;

LiquidCrystal My_LCD(14, 27, 26, 25, 33, 32);
DHT dht(DHTPIN, DHTTYPE);
EnergyMonitor emon1;
WiFiClient espClient;
NodeBridge *bridge;

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

String read_temp()
{ 
  return String(t,2);
}

String read_humidity()
{
  return String(h,2);
}

String read_irms()
{
  return String(amps,2);
}

String read_pow()
{
  return String(watt,2);
}

String read_lcdmsg()
{
  return messageTemp;
}

void write_lcd_msg(const String &payload)
{
  Serial.println("Message arrived: '" + payload + "' ");
  messageTemp = payload;
}

void init_device_node()
{
  bridge = new NodeBridge("SensorsNode1", MQTT_BROKER, MQTT_PORT);
  bridge->begin();
  
  // Wait a bit for ack from server, or poll ackEvent in production
  delay(2000);
  bridge->addPublisher("Temp", "FLOAT", read_temp);
  bridge->addPublisher("Humidity", "FLOAT", read_humidity);
  bridge->addPublisher("Irms", "FLOAT", read_irms);
  bridge->addPublisher("Pow", "FLOAT", read_pow);
  bridge->addSubscriber("LCDMsg", "STRING", read_lcdmsg, write_lcd_msg);
  Serial.println("Node init");
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

  bridge->sendEvent("Temp", read_temp());
  bridge->sendEvent("Humidity", read_humidity());
  bridge->sendEvent("Irms", read_irms());
  bridge->sendEvent("Pow", read_pow());
  
  delay(3000);
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
    delay(3000);
  }
  vTaskDelete( NULL );
}

void loop()
{
  ArduinoOTA.handle(); 
  delay(500);
}
