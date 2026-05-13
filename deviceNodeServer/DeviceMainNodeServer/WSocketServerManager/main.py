#!/usr/bin/python
import sys
import os
from os.path import dirname, realpath, sep, pardir
import time
import zmq
import threading
import json
from threading import Event
import signal

# --- Read and export auth config early so imported modules can use it ---
# Default to the internal compose service name and port 80 if not provided.
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://php-node-service:80")
AUTH_VALIDATE_PATH = os.getenv("AUTH_VALIDATE_PATH", "/api/users/me")

# Ensure these are available to modules that import environment variables at import time
os.environ.setdefault("AUTH_SERVICE_URL", AUTH_SERVICE_URL)
os.environ.setdefault("AUTH_VALIDATE_PATH", AUTH_VALIDATE_PATH)
# ---------------------------------------------------------------------

# Now import application modules (these may read AUTH_* from env)
# Add parent dir and utility paths to sys.path
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "ConfigsUtils")
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")

from websocketHandler import wSocketServerManager
from configsCreate import configsParser
from secretReader import get_secret
from loggerUtils import get_logger
logger = get_logger(__name__)


class handleOnMessage():
    def __init__(self, zmqPath):
        context = zmq.Context()
        #  Socket to talk to server
        logger.info("Connecting to DeviceManager server")
        self.socket = context.socket(zmq.REQ)
        self.zmqPath = zmqPath
        pass

    def connect(self):
        self.socket.connect(self.zmqPath)

    def on_MessageCmd(self, cmdObj):
        logger.info("processing message for web socket server manager with:" + str(cmdObj))
        #deviceManager.executeCMDJson
        #command form:
        '''
        cmd = {
            "method":"executeCMDJson",
            "arg":"{json command obj ...}"
        }
        '''
        cmd = {
            "method":"executeCMDJson",
            "args":cmdObj
        }
        self.socket.send(json.dumps(cmd).encode())
        return self.socket.recv().decode()
    
    def disconnect(self):
        self.socket.close()


if __name__ == "__main__":
    # Read runtime config (existing)
    zmqDeviceManagerConn = os.getenv("DEVICE_MANAGER_LOCAL_CONN", "") # zmqCfg["device-manager-local-conn"]
    webSocketPort = int(os.getenv("WEBSOCKET_PORT", "8112"))

    # Log important runtime configuration including auth service info
    logger.info("Configs for tornado server: ")
    logger.info("ZMQ device manager conn: " + str(zmqDeviceManagerConn))
    logger.info("WebSocket port: " + str(webSocketPort))
    logger.info("Auth service URL: " + str(AUTH_SERVICE_URL))
    logger.info("Auth validate path: " + str(AUTH_VALIDATE_PATH))

    onMsgHandler = handleOnMessage(zmqDeviceManagerConn)
    onMsgHandler.connect()

    WSServer = wSocketServerManager()
    eventStop = Event()
    def sigterm_handler(signum, frame):
        logger.info("stop process")
        eventStop.set()
        WSServer.stop()
        onMsgHandler.disconnect()
    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    WSServer = wSocketServerManager()
    WSServer.init(webSocketPort)
    WSServer.serverListen(onMsgHandler.on_MessageCmd)
    onMsgHandler.disconnect()


