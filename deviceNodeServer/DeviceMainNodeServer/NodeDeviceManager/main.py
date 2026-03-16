import sys
import os
import time
import zmq
import json
from threading import Event
import signal

from os.path import dirname, realpath, sep, pardir
# Get current main.py directory
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "ConfigsUtils")
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")


from deviceDatabaseSync import deviceDatabaseSync
from deviceDataUpgrader import deviceDataUpgrader


from secretReader import get_secret
from loggerUtils import get_logger
logger = get_logger(__name__)

if __name__ == "__main__":
    args = [os.getenv("DB_HOST", ""), os.getenv("DB_NAME", ""), os.getenv("DB_USER", ""), get_secret("DB_PASSWORD")]
    mqttHost = os.getenv("MQTT_BROKER_HOST", "")
    mqttPort = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    mqttKeepalive = int(os.getenv("MQTT_CLIENT_KEEPALIVE", "60"))
    zmqServerPath = os.getenv("DEVICE_MAIN_SERVER_PATH", "")

    logger.info("Device manager started with:")
    logger.info(args)
    logger.info("%s %s %s %s" % (mqttHost, mqttPort, mqttKeepalive, zmqServerPath))

    deviceDbSync = deviceDatabaseSync(args) # source of trut
    time.sleep(2)
    deviceMessageHandler = deviceDataUpgrader(deviceDbSync, mqttHost, mqttPort, mqttKeepalive)
    deviceMessageHandler.startMqttClient()


    eventStop = Event()
    def sigterm_handler(signum, frame):
        logger.info("stop process %s" % (signum, frame))
        eventStop.set()
    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    # init message server
    context = zmq.Context()
    socket = context.socket(zmq.REP)   # REP = reply, each request result in a reply to the same item
    socket.bind(zmqServerPath)        # listen on port 5554 by default
    while not eventStop.is_set():
        try:
            message = socket.recv_string()
            print(f"Received request: {message}")
            commandObj = json.loads(message)
            if "deviceId" not in commandObj:
                logger.error("wrong command %s" % commandObj)
                socket.send_string("ERR_KEY")
                continue
            if commandObj["deviceId"] == "":
                logger.error("null key %s" % commandObj)
                socket.send_string("ERR_NULL")
                continue
            deviceData = deviceDbSync.getDeviceInfo(commandObj["deviceId"])
            if deviceData is None:
                logger.error("device id data not found %s" % deviceData)
                socket.send_string("NOT_FOUND")
                continue
            logger.info("returning %s" % deviceData)
            socket.send_string(json.dumps(deviceData))
        except Exception as e:
            logger.error("an error ocurred %s", e)
    logger.info("ending main node server")

    socket.close()
    context.term()
    pass
