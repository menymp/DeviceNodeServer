#mock script to emulate a device with sensors and actuators

import time
import json
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

manifest = {
        "Name":"MockNode1",
        "RootName":"/MockNode1/",
        "Devices":["digitalSensor","analogSensor","digitalOutput","message"] #
}
jsonManifest = json.dumps(manifest)

def publish(client, topic, value):
    client.publish(topic, value)

def subscribe(client, topic):
    client.subscribe(topic)

def baseMQTTCallback(topic, msg):
    #this callback is to be called when message arrived to subscribed topics
    pass 

def buildMessages(Name, Channel, value, type, mode):
    mqx_tmp =  {
        "Name":Name,
        "Mode":mode,
        "Type":type,
        "Channel": Channel,
        "Value": str(value)
    }
    jsonMsg = json.dumps(mqx_tmp)
    return jsonMsg

def publishData(client, state, digitalOutState, message):
    publish.single(manifest["RootName"] + "manifest", jsonManifest, "broker")
    sensorState = "false"
    analogValue = 0

    if (state):
        sensorState = "true"
        analogValue = 22
    else:
        sensorState = "false"
        analogValue = 55

    baseChanel = manifest["RootName"] + "digitalSensor"
    jsonObj = buildMessages("digitalSensor", manifest["RootName"] + "digitalSensor", sensorState, "STRING", "PUBLISHER")
    publish.single(baseChanel, jsonObj, "broker")

    baseChanel = manifest["RootName"] + "analogSensor"
    jsonObj = buildMessages("analogSensor", manifest["RootName"] + "analogSensor", analogValue, "STRING", "PUBLISHER")
    publish.single(baseChanel, jsonObj, "broker")

    baseChanel = manifest["RootName"] + "digitalOutput"
    jsonObj = buildMessages("digitalOutput", manifest["RootName"] + "digitalOutput", digitalOutState, "STRING", "SUBSCRIBER")
    publish.single(baseChanel, jsonObj, "broker")

    baseChanel = manifest["RootName"] + "message"
    jsonObj = buildMessages("message", manifest["RootName"] + "message", message, "STRING", "SUBSCRIBER")
    publish.single(baseChanel, jsonObj, "broker")
    pass
        

if __name__ == "__main__":
    tmpState = True
    message = ""
    digitalOutState = False

    def on_message(client, userdata, msg):
        global digitalOutState
        global message
        m_decode=str(msg.payload.decode("utf-8","ignore"))
        if (msg.topic == ( manifest["RootName"] + "digitalOutput" + "/value")):
            digitalOutState = m_decode == "on"
            print("current digital output state: " + str(digitalOutState))
            pass
        if (msg.topic == ( manifest["RootName"] + "message" + "/value")):
            message = m_decode
            print("current message: " + str(message))
            pass
        pass

    def on_connect(client, userdata, flags, rc):
        client.subscribe(manifest["RootName"] + "digitalOutput" + "/value")
        client.subscribe(manifest["RootName"] + "message" + "/value")
        pass

    client = mqtt.Client()
    client.on_message = on_message
    client.on_connect = on_connect
    client.connect("broker", "port","keepalive")
    
    while True:
        tmpState = not tmpState
        publishData(client, tmpState, digitalOutState, message)
        time.sleep(4)
    pass