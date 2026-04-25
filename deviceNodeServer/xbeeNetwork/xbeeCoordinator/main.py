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

import json
import sys
import os
import time
import signal
import logging
from pathlib import Path

# allow local libs if needed (adjust paths if your project layout differs)
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT / "DButils"))
sys.path.append(str(ROOT / "Libraries"))
sys.path.append(str(ROOT / "DockerUtils"))

# configure logging
LOG_LEVEL = os.environ.get("WORKER_LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("xbee.main")

# import controller (adjust module name/path if different)
from XbeeNetworkController import XbeeNetworkController


def read_config_file(path: str = "./configs.json") -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.exception("Failed to read config file %s", path)
        return {}


def build_configs() -> dict:
    # load file config first, then overlay environment variables
    cfg = read_config_file("./configs.json")

    def env_or_cfg(key: str, default=None):
        return os.getenv(key.upper().replace("-", "_"), cfg.get(key, default))

    configs = {
        "name": env_or_cfg("name", cfg.get("name", "")),
        "mqtt-host": env_or_cfg("mqtt-host", cfg.get("mqtt-host", "localhost")),
        "mqtt-port": int(env_or_cfg("mqtt-port", cfg.get("mqtt-port", 1883))),
        "manifest-publish-delay": int(env_or_cfg("manifest-publish-delay", cfg.get("manifest-publish-delay", 6))),
        "comm-port-path": env_or_cfg("comm-port-path", cfg.get("comm-port-path", "")),
        "com-baud-rate": int(env_or_cfg("com-baud-rate", cfg.get("com-baud-rate", 9600))),
        "discovery-time": int(env_or_cfg("discovery-time", cfg.get("discovery-time", 120))),
        "keepalive": int(env_or_cfg("keepalive", cfg.get("keepalive", 60))),
        "sampling": int(env_or_cfg("sampling", cfg.get("sampling", 6))),
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

    # graceful shutdown handler
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
                # publish manifests for all managed nodes
                controller.publish_all_manifests()
            except Exception:
                logger.exception("Error while publishing manifests")
            # sleep in small increments so we can react quickly to signals
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
