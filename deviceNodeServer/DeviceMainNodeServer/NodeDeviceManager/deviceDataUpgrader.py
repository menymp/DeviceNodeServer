import threading
from threading import Event
from threading import Timer
import sys
import queue
import time
import json
import paho.mqtt.client as mqtt
from os.path import dirname, realpath, sep, pardir
# Get current main.py directory
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DButils")
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")


from loggerUtils import get_logger
logger = get_logger(__name__)

#Handles device requests by hearing messages over topic /inbound
# creates devices in the db if not exists
# updates its db measurement states
# notifies device manager from new devices to add by zmq
class deviceDataUpgrader():
    broker_registration_path = "/inbound"
    broker_validation_path = "/node_name_request"
    
    def __init__(self, deviceSyncInstance, broker, port = 1883, keepalive = 60):
        logger.info("init device message handler %s %s %s" % (broker, port, keepalive))
        self.deviceSyncInstance = deviceSyncInstance
        self.path = broker #poner el manifest en el path NOTA IMPORTANTE
        self.mqttBrokerPath = broker
        self.port = port
        self.keepalive = keepalive

    def startMqttClient(self):
        logger.info("starting client mqtt")
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._handleIncomingMessage
        self.client.connect(self.mqttBrokerPath, self.port, self.keepalive)
        self.taskListen = threading.Thread(target=self._handle, args=())
        self.taskListen.start()
        pass
    
    def _on_connect(self, client, userdata, flags, rc):
        logger.info("Server connected to broker")
        self.client.subscribe(self.broker_registration_path)
        self.client.subscribe(self.broker_validation_path)
        pass
    
    # manages the main message threading
    def _handle(self):
        self.client.loop_forever()
        pass

    '''
    message should have the following form
    {
        "Name":"MenyGardenNode1",
        "RootName":"/MenyGardenNode1/",
        "ip": "x.x.x.x",
        "Devices": [
            {
                "Name":"PirSensor",
                "Mode":"PUBLISHER",
                "Type":"STRING",
                "Channel": "/MenyGardenNode1/PirSensor",
                "Value": "69.69"
            },
            {
                "Name":"WaterPump",
                "Mode":"SUBSCRIBER",
                "Type":"STRING",
                "Channel":"/MenyNode1/WaterSolenoid/state",
                "Value": "ON"
            }
        ]

    }
    '''
    def _handleIncomingMessage(self, client, userdata, msg):
        logger.info("received message")
        logger.info(msg)
        if msg.topic == self.broker_registration_path:
            logger.info("Registration message")
            self._handle_registration_message(msg)
        if msg.topic == self.broker_validation_path:
            self._handle_validation_request(msg)
        pass

    #handle each device call to main register thread
    def _handle_registration_message(self, msg):
        try:
            m_decode=str(msg.payload.decode("utf-8","ignore"))
            logger.info("manifest discovered %s" % (m_decode))
            nodeManifest = json.loads(m_decode)
            # Integrity validation
            nodeName = nodeManifest["Name"]
            RootName = nodeManifest["RootName"]
            macAddr = nodeManifest["mac_addr"]
            Devices = nodeManifest["Devices"]

            if nodeName == "" or RootName == "" or macAddr == "" or Devices is None:
                logger.error("invalid request form")
                return
            self.deviceSyncInstance.updateNode(nodeManifest)

        except Exception as e:
            logger.error("an error ocurred processing device registration request %s", e)
        pass

    def _handle_validation_request(self, msg):
        try:
            m_decode=str(msg.payload.decode("utf-8","ignore"))
            logger.info("registration request %s" % (m_decode))
            nodeValidationRequest = json.loads(m_decode)
            # Integrity validation
            nodeName = nodeValidationRequest["Name"]
            nodeAcknowledgePath = nodeValidationRequest["AcknowledgePath"] #the path where the node is waiting confirmation
            nodeMacAddress = nodeValidationRequest["MacAddress"] #the path where the node is waiting confirmation
            if nodeName == "" or nodeAcknowledgePath == "" or nodeMacAddress == "":
                logger.error("invalid request validation form %s %s %s" % (nodeName, nodeAcknowledgePath, nodeMacAddress))
                return
            if not self.deviceSyncInstance.nodeAcknowledge(nodeName, nodeMacAddress):
                # return a failure name adquisition if name already exists in the server instance
                logger.error("Node name [%s, %s] in use " % (nodeName, nodeMacAddress))
                self.client.publish(topic = nodeAcknowledgePath, payload = "ERR_ACK")
                return
            logger.info("Node name %s successfully registered " % (nodeName))
            self.client.publish(topic = nodeAcknowledgePath, payload = "SUCCESS_ACK")
        except Exception as e:
            logger.error("an error ocurred processing device validation request %s", e)
        pass

    def __exit__(self):
        try:
            self.client.disconnect() # disconnect gracefully
            self.client.loop_stop() # stops network loop
        except:
            pass
        pass