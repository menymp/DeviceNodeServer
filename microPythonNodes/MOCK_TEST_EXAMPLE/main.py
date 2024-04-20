#mock script to emulate a device with sensors and actuators

import time
import json
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

broker = ""

manifest = {
        "Name":"MockNode1",
        "RootName":"/MockNode1/",
        "Devices":["digitalSensor","analogSensor","digitalOutput","message"] #
}
jsonManifest = json.dumps(manifest)

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
    client.publish(manifest["RootName"] + "manifest", jsonManifest)
    sensorState = "false"
    analogValue = 0

    if (state):
        sensorState = "true"
        analogValue = 22
    else:
        sensorState = "false"
        analogValue = 55
    
    if digitalOutState:
        digitalOutString = "on"
    else:
        digitalOutString = "off"

    baseChanel = manifest["RootName"] + "digitalSensor"
    jsonObj = buildMessages("digitalSensor", manifest["RootName"] + "digitalSensor", sensorState, "STRING", "PUBLISHER")
    client.publish(baseChanel, jsonObj)

    baseChanel = manifest["RootName"] + "analogSensor"
    jsonObj = buildMessages("analogSensor", manifest["RootName"] + "analogSensor", analogValue, "STRING", "PUBLISHER")
    client.publish(baseChanel, jsonObj)

    baseChanel = manifest["RootName"] + "digitalOutput"
    jsonObj = buildMessages("digitalOutput", manifest["RootName"] + "digitalOutput/value", digitalOutString, "STRING", "SUBSCRIBER")
    client.publish(baseChanel, jsonObj)

    baseChanel = manifest["RootName"] + "message"
    jsonObj = buildMessages("message", manifest["RootName"] + "message/value", message, "STRING", "SUBSCRIBER")
    client.publish(baseChanel, jsonObj)
    pass
        

if __name__ == "__main__":
    tmpState = True
    message = ""
    digitalOutState = False

    def on_message(client, userdata, msg):
        global digitalOutState
        global message
        m_decode=str(msg.payload.decode("utf-8","ignore"))
        print("received " + m_decode)
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
    client.connect(broker, 1883,60)
    client.loop_start()
    
    while True:
        tmpState = not tmpState
        publishData(client, tmpState, digitalOutState, message)
        time.sleep(4)
    client.loop_stop()
    pass