//MQTT Node Firmware for esp 8266 GARDEN
//menymp
#include <ArduinoJson.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#define SENSOR_PIR 0
#define WATER_SOLENOID 2

const char* ssid = "";
const char* password = "";
const char* mqtt_server = "";

WiFiClient wlanclient;
PubSubClient mqttClient(wlanclient);

char out[600];
size_t cntBuff = 0;
StaticJsonDocument<600> manifest;

char S_out[600];
size_t S_cntBuff = 0;
StaticJsonDocument<200> Device1;

int cntA = 0;
String messageTemp;

void mqttCallback(char *topic, byte *payload, unsigned int length) {
  Serial.print ("Message arrived on Topic:");
  Serial.print (topic);

  if (String(topic) == "/MenyNode1/WatterSolenoid/state") 
  {
    messageTemp = "";
    for (int i = 0; i < length; i++) 
    {
      Serial.print((char)payload[i]);
      messageTemp += (char)payload[i];
    }

    if(messageTemp == "ON")
    {
      digitalWrite(WATER_SOLENOID,LOW);
    }
    if(messageTemp == "OFF")
    {
      digitalWrite(WATER_SOLENOID,HIGH);
    }
    Serial.println();
    //pending
  }
}

void setup()
{  
  Serial.begin(9600);
  CreateManifest();

  pinMode(SENSOR_PIR,INPUT);
  pinMode(WATER_SOLENOID,OUTPUT);
  digitalWrite(WATER_SOLENOID,HIGH);
  setup_wifi();
  
  mqttClient.setServer (mqtt_server,1883);
  mqttClient.setCallback(mqttCallback);
}

void CreateManifest()
{
  manifest["Name"] = "MenyNode1";
  manifest["RootName"] = "/MenyNode1/";
  JsonArray Devices = manifest.createNestedArray("Devices");
  
  Devices.add("PirSensor");
  Devices.add("WaterSolenoid");
  cntBuff =serializeJson(manifest, out);
}

void setup_wifi() 
{
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

void reconnect() 
{
  // Loop until we're reconnected
  while (!mqttClient.connected()) 
  {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (mqttClient.connect("MenyGardenUnit1_MechLab")) 
    {
      Serial.println("connected");
      mqttClient.subscribe("/MenyNode1/WatterSolenoid/state");
    } 
    else 
    {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void PublishData()
{
    Serial.println();
    Serial.print("num:");
    Serial.println(cntBuff);
    Serial.print(out);
    if(cntA > 6)
    {
      cntA = 0;
      mqttClient.publish("/MenyPir1/manifest", out, cntBuff );//

       Device1["Name"] = "WatterSolenoid";
       Device1["Mode"] = "SUBSCRIBER";
       Device1["Type"] = "STRING";
       Device1["Channel"] = "/MenyNode1/WatterSolenoid/state";
       Device1["Value"] = messageTemp;
       S_cntBuff =serializeJson(Device1, S_out);
       mqttClient.publish("/MenyNode1/WatterSolenoid", S_out, S_cntBuff );//
    }
}

void loop()
{
  if (!mqttClient.connected()) 
  {
    reconnect();
  }
  mqttClient.loop();
  delay(500);
}
