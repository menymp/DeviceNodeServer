'''
Network adapter for device manager system and xbee shield
menymp

this app works as a sub register that allow receiving and transfer of
data from and to xbee network.

The application starts with a discovery of each device and creates a list of devices.
this is performed periodicaly and allow to incorporate new devices into the network.

with the existing devices, a manifest is then created in the same way as other mqtt devices

then each device information is forward relayed to a subtopic for publisher and subscribers
in the case of subscribers, an aditional subscription is created in order to accept incomming commands.


In construction ...

#OK: a new logic is needed, instead of the client devices to always transmit state, do a continuous
device scanning by the coordinator AND each time a new message arrives, use a queue to store every transaction
and process them in order.
Apr 2026: The system was improved to seamesly integrate with the existing manifest structure

important: take in account that this system is slow as the long range rf communication is slow

# Entrypoint for the XBee coordinator service.
# Uses XbeeNetworkController to manage discovered XBee nodes and create node_bridge instances.
#
# Behavior:
#  - Loads configuration from ./configs.json if present, otherwise from environment variables.
#  - Starts the XBee network controller.
#  - Periodically publishes manifests for all managed nodes.
#  - Handles SIGTERM for graceful shutdown.
'''

# main.py
# Entrypoint for the XBee coordinator service.
import os
import signal
import sys
import time
import logging

from XbeeNetworkController import XbeeNetworkController

LOG_LEVEL = os.environ.get("WORKER_LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("xbee.main")


def build_configs() -> dict:
    """
    Build configs exclusively from environment variables (no configs.json).
    Expected env vars (as provided in docker-compose):
      - XBEE_COORDINATOR_NAME
      - XBEE_COORDINATOR_MANIFEST_PUBLISH_DELAY
      - XBEE_COORDINATOR_TTY_PORT
      - XBEE_COORDINATOR_BAUDRATE
      - MQTT_BROKER_HOST
      - MQTT_BROKER_PORT
      - KEEPALIVE (optional)
      - SAMPLING (optional)
      - DISCOVERY_TIME (optional, kept for coordinator compatibility)
    """
    def env(key, default=None):
        return os.getenv(key, default)

    configs = {
        "name": env("XBEE_COORDINATOR_NAME", ""),
        "manifest-publish-delay": int(env("XBEE_COORDINATOR_MANIFEST_PUBLISH_DELAY", "6")),
        "comm-port-path": env("XBEE_COORDINATOR_TTY_PORT", "/dev/ttyUSB0"),
        "com-baud-rate": int(env("XBEE_COORDINATOR_BAUDRATE", "9600")),
        "mqtt-host": env("MQTT_BROKER_HOST", "localhost"),
        "mqtt-port": int(env("MQTT_BROKER_PORT", "1883")),
        "keepalive": int(env("KEEPALIVE", "60")),
        "sampling": int(env("SAMPLING", "6")),
        "discovery-time": int(env("DISCOVERY_TIME", "30")),
    }
    return configs


def main():
    configs = build_configs()
    logger.info("Starting XBee coordinator service with config: %s", {
        "name": configs.get("name"),
        "mqtt-host": configs.get("mqtt-host"),
        "mqtt-port": configs.get("mqtt-port"),
        "comm-port-path": configs.get("comm-port-path"),
        "com-baud-rate": configs.get("com-baud-rate"),
        "discovery-time": configs.get("discovery-time"),
        "manifest-publish-delay": configs.get("manifest-publish-delay"),
    })

    controller = XbeeNetworkController(configs)

    stop_requested = {"flag": False}

    def _signal_handler(signum, frame):
        logger.info("Signal %s received, stopping...", signum)
        stop_requested["flag"] = True

    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    try:
        controller.start()
    except Exception:
        logger.exception("Failed to start XbeeNetworkController")
        return 1

    publish_delay = int(configs.get("manifest-publish-delay", 6))
    try:
        while not stop_requested["flag"]:
            try:
                # publish manifests for all managed nodes (node_bridge will use last-known values)
                controller.publish_all_manifests()
            except Exception:
                logger.exception("Error while publishing manifests")
            slept = 0.0
            interval = 0.5
            while slept < publish_delay and not stop_requested["flag"]:
                time.sleep(interval)
                slept += interval
    except Exception:
        logger.exception("Unexpected error in main loop")
    finally:
        logger.info("Shutting down XBee coordinator")
        try:
            controller.stop()
        except Exception:
            logger.exception("Error while stopping controller")
        logger.info("Shutdown complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
