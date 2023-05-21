//MQTT Node Firmware for esp 8266 GARDEN
//menymp
#include <ArduinoJson.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#define OUTPUT_PIN1 14  //d5
#define OUTPUT_PIN2 12  //d6
#define OUTPUT_PIN3 13  //d7
#define OUTPUT_PIN4 15  //d2

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
String messageTemp1 = "OFF";
String messageTemp2 = "OFF";
String messageTemp3 = "OFF";
String messageTemp4 = "OFF";

void mqttCallback(char *topic, byte *payload, unsigned int length) {
  Serial.print ("Message arrived on Topic:");
  Serial.print (topic);

  if (String(topic) == "/MenyOutputs1/Output1/state") 
  {
    messageTemp1 = "";
    for (int i = 0; i < length; i++) 
    {
      Serial.print((char)payload[i]);
      messageTemp1 += (char)payload[i];
    }

    if(messageTemp1 == "ON")
    {
      digitalWrite(OUTPUT_PIN1,HIGH);
    }
    if(messageTemp1 == "OFF")
    {
      digitalWrite(OUTPUT_PIN1,LOW);
    }
    Serial.println();
  }

    if (String(topic) == "/MenyOutputs1/Output2/state") 
  {
    messageTemp2 = "";
    for (int i = 0; i < length; i++) 
    {
      Serial.print((char)payload[i]);
      messageTemp2 += (char)payload[i];
    }

    if(messageTemp2 == "ON")
    {
      digitalWrite(OUTPUT_PIN2,HIGH);
    }
    if(messageTemp2 == "OFF")
    {
      digitalWrite(OUTPUT_PIN2,LOW);
    }
    Serial.println();
  }

    if (String(topic) == "/MenyOutputs1/Output3/state") 
  {
    messageTemp3 = "";
    for (int i = 0; i < length; i++) 
    {
      Serial.print((char)payload[i]);
      messageTemp3 += (char)payload[i];
    }

    if(messageTemp3 == "ON")
    {
      digitalWrite(OUTPUT_PIN3,HIGH);
    }
    if(messageTemp3 == "OFF")
    {
      digitalWrite(OUTPUT_PIN3,LOW);
    }
    Serial.println();
  }

    if (String(topic) == "/MenyOutputs1/Output4/state") 
  {
    messageTemp4 = "";
    for (int i = 0; i < length; i++) 
    {
      Serial.print((char)payload[i]);
      messageTemp4 += (char)payload[i];
    }

    if(messageTemp4 == "ON")
    {
      digitalWrite(OUTPUT_PIN4,HIGH);
    }
    if(messageTemp4 == "OFF")
    {
      digitalWrite(OUTPUT_PIN4,LOW);
    }
    Serial.println();
  }
}

void setup()
{  
  Serial.begin(9600);
  

  pinMode(OUTPUT_PIN1,OUTPUT);
  pinMode(OUTPUT_PIN2,OUTPUT);
  pinMode(OUTPUT_PIN3,OUTPUT);
  pinMode(OUTPUT_PIN4,OUTPUT);
  digitalWrite(OUTPUT_PIN1,LOW);
  digitalWrite(OUTPUT_PIN2,LOW);
  digitalWrite(OUTPUT_PIN3,LOW);
  digitalWrite(OUTPUT_PIN4,LOW);
  setup_wifi();
  CreateManifest();
  mqttClient.setServer (mqtt_server,1883);
  mqttClient.setCallback(mqttCallback);
}

void CreateManifest()
{
  manifest["Name"] = "MenyOutputs1";
  manifest["RootName"] = "/MenyOutputs1/";
  JsonArray Devices = manifest.createNestedArray("Devices");
  
  Devices.add("Ouptut1");
  Devices.add("Output2");
  Devices.add("Output3");
  Devices.add("Output4");
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
    if (mqttClient.connect("MenyOutputsUnit1_MechLab")) 
    {
      Serial.println("connected");
      mqttClient.subscribe("/MenyOutputs1/Output1/state");
      mqttClient.subscribe("/MenyOutputs1/Output2/state");
      mqttClient.subscribe("/MenyOutputs1/Output3/state");
      mqttClient.subscribe("/MenyOutputs1/Output4/state");
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

    if(cntA > 6)
    {
      cntA = 0;
      mqttClient.publish("/MenyOutputs1/manifest", out, cntBuff );//
      
      Serial.println(out);

       Device1["Name"] = "MenyOutputs1";
       Device1["Mode"] = "SUBSCRIBER";
       Device1["Type"] = "STRING";
       Device1["Channel"] = "/MenyOutputs1/Output1/state";
       Device1["Value"] = messageTemp1;
       S_cntBuff =serializeJson(Device1, S_out);
       mqttClient.publish("/MenyOutputs1/Output1", S_out, S_cntBuff );//
       Serial.println(S_out);
       Device1["Name"] = "MenyOutputs1";
       Device1["Mode"] = "SUBSCRIBER";
       Device1["Type"] = "STRING";
       Device1["Channel"] = "/MenyOutputs1/Output2/state";
       Device1["Value"] = messageTemp2;
       S_cntBuff =serializeJson(Device1, S_out);
       mqttClient.publish("/MenyOutputs1/Output2", S_out, S_cntBuff );//

       Device1["Name"] = "MenyOutputs1";
       Device1["Mode"] = "SUBSCRIBER";
       Device1["Type"] = "STRING";
       Device1["Channel"] = "/MenyOutputs1/Output3/state";
       Device1["Value"] = messageTemp3;
       S_cntBuff =serializeJson(Device1, S_out);
       mqttClient.publish("/MenyOutputs1/Output3", S_out, S_cntBuff );//

       Device1["Name"] = "MenyOutputs1";
       Device1["Mode"] = "SUBSCRIBER";
       Device1["Type"] = "STRING";
       Device1["Channel"] = "/MenyOutputs1/Output4/state";
       Device1["Value"] = messageTemp4;
       S_cntBuff =serializeJson(Device1, S_out);
       mqttClient.publish("/MenyOutputs1/Output4", S_out, S_cntBuff );//
    }
    cntA++;
//    if(digitalRead(SENSOR_PIR))
//    {
//       Device1["Name"] = "PirSensor";
//       Device1["Mode"] = "PUBLISHER";
//       Device1["Type"] = "STRING";
//       Device1["Channel"] = "/MenyPir1/PirSensor";
//       Device1["Value"] = "MOTION_DETECTED";
//       S_cntBuff =serializeJson(Device1, S_out);
//       mqttClient.publish("/MenyPir1/PirSensor", S_out, S_cntBuff );//
//    }
}

void loop()
{
  if (!mqttClient.connected()) 
  {
    reconnect();
  }
  mqttClient.loop();
  delay(500);
  PublishData();
}
