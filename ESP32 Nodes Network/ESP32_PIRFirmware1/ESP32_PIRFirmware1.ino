//MQTT Node Firmware for esp 8266 pir SENSOR 
//menymp
#include <ArduinoJson.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#define SENSOR_PIR 3
//#define SENSOR_VIBRATION 3

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
int PIRVal = 0;
int VRVal = 0;

void mqttCallback(char *topic, byte *payload, unsigned int length) {
  //Serial.print ("Message arrived on Topic:");
  //Serial.print (topic);
}

void setup()
{  
  //Serial.begin(9600);
  CreateManifest();

  pinMode(SENSOR_PIR,INPUT);
  //pinMode(SENSOR_VIBRATION,INPUT);

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
  //Devices.add("VibrationSensor");
  cntBuff =serializeJson(manifest, out);
}

void setup_wifi() 
{
  delay(10);
  // We start by connecting to a WiFi network
  //Serial.println();
  //Serial.print("Connecting to ");
  //Serial.println(ssid);
  
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    //Serial.print(".");
  }
  //Serial.println("");
 // Serial.println("WiFi connected");
  //Serial.println("IP address: ");
  //Serial.println(WiFi.localIP());
}

void reconnect() 
{
  // Loop until we're reconnected
  while (!mqttClient.connected()) 
  {
    //Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (mqttClient.connect("MenyPirSensor1_MechLab")) 
    {
      //Serial.println("connected");
    } 
    else 
    {
      //Serial.print("failed, rc=");
      //Serial.print(mqttClient.state());
      //Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void PublishData()
{
    //Serial.println();
    //Serial.print("num:");
    //Serial.println(cntBuff);
    //Serial.print(out);
    cntA ++;
    if(cntA > 6)
    {
      cntA = 0;
      mqttClient.publish("/MenyPir1/manifest", out, cntBuff );//
    }
    //Serial.print(digitalRead(SENSOR_PIR));
    //Serial.print(digitalRead(SENSOR_VIBRATION));
    if(digitalRead(SENSOR_PIR))
    {
      
       Device1["Name"] = "PirSensor";
       Device1["Mode"] = "PUBLISHER";
       Device1["Type"] = "STRING";
       Device1["Channel"] = "/MenyPir1/PirSensor";
       Device1["Value"] = "MOTION_DETECTED";
       S_cntBuff =serializeJson(Device1, S_out);
       mqttClient.publish("/MenyPir1/PirSensor", S_out, S_cntBuff );//
       
    }
//    if(digitalRead(SENSOR_VIBRATION) != VRVal)
//    {
//       VRVal = digitalRead(SENSOR_VIBRATION);
//       Device1["Name"] = "VibrationSensor";
//       Device1["Mode"] = "PUBLISHER";
//       Device1["Type"] = "STRING";
//       Device1["Channel"] = "/MenyPir1/VibrationSensor";
//       Device1["Value"] = "VIBRATION_DETECTED";
//       S_cntBuff =serializeJson(Device1, S_out);
//       mqttClient.publish("/MenyPir1/VibrationSensor", S_out, S_cntBuff );//
//    }
}

void loop()
{
  if (!mqttClient.connected()) 
  {
    reconnect();
  }
  PublishData();
  mqttClient.loop();
  delay(500);
}
