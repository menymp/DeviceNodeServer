from wifi import wlanConnect
from mqtt import connectMQTT, publish, subscribe
import json

manifest = {
        "Name":"MenySMDOven1",
        "RootName":"/MenySMDOven1/",
        "Devices":["oven_state", "elapsed_time", "command"]
}
jsonManifest = json.dumps(manifest)

class remoteInterface():
    def __init__(self, configs):
        self.configs_d = configs
        self.configs(configs)
        self.current_cmd = "None"
        pass

    def connectWifi(self, ssid, pwd):
        self.configs["wifi_ssid"] = ssid
        self.configs["wifi_pwd"] = pwd
        # ToDo: properly terminate current connection if any
        #       save configs once ready
        self.wlanObj = wlanConnect(configs["wifi_ssid"],configs["wifi_pwd"])
        self.connectMqtt()
    
    def connectMqtt(self, clientId = None, broker = None):
        #ToDo: add proper configs calls if no parameter are provided
        subscribe(client, "/MenySMDOven1/command/value")
        pass

    def configs(self, configs):
        self.wlanObj = wlanConnect(configs["wifi_ssid"],configs["wifi_pwd"])
        self.mqttClient = connectMQTT(configs["mqtt_client_id"], configs["mqtt_broker"], self._baseMQTTCallback)

    def _baseMQTTCallback(self, topic, msg):
        print('received from: ' + str(topic) + 'msg: ' + str(msg))
        
        if topic == b'/MenySMDOven1/command/value':
            #ToDo: in the future use this command to teleoperate the oven
            self.current_cmd = msg.decode("utf-8")
    
    def buildPublish(Name, Channel, value, Mode):
        mqx_tmp =  {
            "Name":Name,
            "Mode":Mode,
            "Type":"STRING",
            "Channel":Channel,
            "Value":str(value)
        }
        jsonMsg = json.dumps(mqx_tmp)
        return jsonMsg
    
    def getConnState(self):
        #ToDo: get if connected mqtt and wifi
        return wifi_state, mqtt_state

    def publishData(self, currentState, elapsedTime):

        wifi_state, mqtt_state = self.getConnState()
        if(!wifi_state or !mqtt_state):
           return

        publish(self.mqttClient, manifest["RootName"] + "manifest", jsonManifest)

        jsonMsg = self.buildPublish("oven_state", manifest["RootName"] + "oven_state", currentState, "PUBLISHER")
        publish(self.mqttClient, manifest["RootName"] + "oven_state", jsonMsg)
        
        jsonMsg = self.buildPublish("elapsed_time", manifest["RootName"] + "elapsed_time", elapsedTime, "PUBLISHER")
        publish(self.mqttClient, manifest["RootName"] + "elapsed_time", jsonMsg)

        jsonMsg = self.buildPublish("command", manifest["RootName"] + "command", self.current_cmd, "SUBSCRIBER")
        publish(self.mqttClient, manifest["RootName"] + "command/value", jsonMsg)
        pass