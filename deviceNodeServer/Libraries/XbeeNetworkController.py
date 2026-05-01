# XbeeNetworkController.py
#
# Integrates XBee coordinator with node_bridge instances.
# For every discovered XBee remote device we create a node_bridge instance
# that exposes the remote device's manifest and events to the MQTT broker
# using the same node_bridge protocol used elsewhere in the project.
#
# Expected dependencies (adjust import paths to your project layout):
#   - xbee_coordinator.XbeeNetCoordinator (drop-in coordinator from earlier)
#   - node_bridge.node_bridge (node bridge class)
#   - logger.logger (project logging util)
#
# Behavior summary:
#   - On discovery: ensure a node_bridge exists for the remote address.
#   - On manifest: create publisher/subscriber devices on the node_bridge and store initial values.
#   - On event: forward publisher events to node_bridge.send_event (publishes to MQTT).
#   - On MQTT command (subscriber callback): send command JSON to the XBee node via coordinator.
#
# Usage:
#   controller = XbeeNetworkController(configs)
#   controller.start()
#   ...
#   controller.stop()
#
# Integrates XBee coordinator with node_bridge instances.
# For every discovered XBee remote device we create a node_bridge instance
# that exposes the remote device's manifest and events to the MQTT broker
# using the same node_bridge protocol used elsewhere in the project.
#
# This version ALWAYS uses the XBee 64-bit address (derived) as the mac_addr
# passed to node_bridge. Manifest-provided MACs are ignored.

# XbeeNetworkController.py
# Uses XbeeNetCoordinator to manage node_bridge instances for each discovered XBee remote.
import json
import logging
import threading
import time
from typing import Dict, Any, List, Optional

from XbeeNetCoordinator import XbeeNetCoordinator
from node_bridge import node_bridge
from DButils.dbActions import dbDevicesActions

logger = logging.getLogger("XbeeNetworkController")


class XbeeNetworkController:
    """
    Controller that maps each discovered XBee remote device to a node_bridge instance.
    This version:
      - Uses environment-driven configs (passed in)
      - Does NOT run discovery; devices send manifests/events periodically
      - Instantiates node_bridge when a manifest arrives (manifest-driven creation)
      - Keeps last-known device state per node and updates it on events and commands
      - Removes node_bridge instances after INACTIVITY_TIMEOUT seconds of no messages
    """

    INACTIVITY_TIMEOUT = 120  # seconds to consider a node inactive and remove it

    def __init__(self, configs: Dict[str, Any]):
        self.configs = configs
        discovery_time = configs.get("discovery-time", 120)
        self.coordinator = XbeeNetCoordinator(discovery_time=discovery_time)

        # Map remote address (string) -> node_bridge instance
        self._node_bridges: Dict[str, node_bridge] = {}

        # Map remote address -> device state dict: deviceName -> lastValue (strings)
        self._device_states: Dict[str, Dict[str, str]] = {}

        # Map remote address -> last seen timestamp (time.time())
        self._last_seen: Dict[str, float] = {}

        # Lock to protect maps
        self._lock = threading.RLock()

        # background cleaner thread
        self._cleaner_thread = threading.Thread(target=self._cleaner_loop, daemon=True)
        self._cleaner_stop = threading.Event()
        
        # Retriving valid types:
        self.dbDevicesActions1 = dbDevicesActions()
        self.dbDevicesActions1.initConnector(configs.get("db-user"),configs.get("db-password"),configs.get("db-host"),configs.get("db-name"))
        self.valid_types = self.dbDevicesActions1.getValidDeviceTypes()
        logger.info("Got device data types: " + str(self.valid_types))

        logger.info(
            "XbeeNetworkController initialized: mqtt=%s:%s comm=%s@%s discovery=%s",
            configs.get("mqtt-host"),
            configs.get("mqtt-port"),
            configs.get("comm-port-path"),
            configs.get("com-baud-rate"),
            discovery_time,
        )
    
    def map_valid_type(self, encoded_type):
        expanded_type = ""
        if encoded_type == "F":
            expanded_type = "FLOAT"
        if encoded_type == "S":
            expanded_type = "STRING"
        if encoded_type == "I":
            expanded_type = "INT"
        
        if expanded_type not in self.valid_types:
            logger.info("Invalid device data type: " + str(expanded_type))
            return None

        return expanded_type

    def start(self):
        logger.info("Starting XbeeNetworkController")
        # initialize coordinator with callbacks
        self.coordinator.init(
            self.configs["comm-port-path"],
            self.configs["com-baud-rate"],
            message_received_callback=self._message_received_callback,
            sync_devices_callback=None
        )
        self.coordinator.start()
        self._cleaner_stop.clear()
        self._cleaner_thread.start()
        logger.info("Coordinator started and cleaner thread running")

    def stop(self):
        logger.info("Stopping XbeeNetworkController")
        self._cleaner_stop.set()
        if self._cleaner_thread.is_alive():
            self._cleaner_thread.join(timeout=2.0)
        # Disable and remove node bridges
        with self._lock:
            for addr, nb in list(self._node_bridges.items()):
                try:
                    nb.disable()
                    logger.info("Disabled node_bridge for %s", addr)
                except Exception:
                    logger.exception("Error disabling node_bridge for %s", addr)
            self._node_bridges.clear()
            self._device_states.clear()
            self._last_seen.clear()
        # Stop coordinator
        try:
            self.coordinator.stop()
            logger.info("Coordinator stopped")
        except Exception:
            logger.exception("Error stopping coordinator")

    # -------------------------
    # Coordinator callback
    # -------------------------
    def _message_received_callback(self, address64bit: str, data: str):
        """
        Called by coordinator when a frame arrives from a remote device.
        data is the raw payload string from the XBee node (e.g., "E:...#" or "M...#").
        """
        addr = str(address64bit)
        logger.info("Message received from %s: %s", addr, data)
        # update last seen
        with self._lock:
            self._last_seen[addr] = time.time()

        payload = data.strip()
        # Manifest messages start with 'M'
        if payload.startswith("M"):
            try:
                devices = self._parse_compact_manifest(payload)
                logger.info("Manifest received from %s with %d devices", addr, len(devices))
                # Manifest-driven creation/update: ensure node_bridge exists and update devices
                self._handle_manifest(addr, devices)
            except Exception:
                logger.exception("Failed to parse manifest from %s payload=%s", addr, payload)
        # Event messages start with 'E:'
        elif payload.startswith("E:"):
            try:
                ev = self._parse_compact_event(payload)
                logger.info("Event received from %s device=%s value=%s", addr, ev.get("Name"), ev.get("Value"))
                self._handle_event(addr, ev)
            except Exception:
                logger.exception("Failed to parse event from %s payload=%s", addr, payload)
        else:
            logger.debug("Unhandled payload format from %s: %s", addr, payload)

    # -------------------------
    # Parsing helpers
    # -------------------------
    def _parse_compact_manifest(self, payload: str) -> List[Dict[str, str]]:
        """
        Parse payload like:
          M2:PirSensor,P,F,70.89;WaterPump,S,S,#
        Returns list of dicts: {Name, Mode, Type, Value}
        """
        if payload.endswith("#"):
            payload = payload[:-1]
        colon = payload.find(":")
        if colon < 0:
            raise ValueError("manifest missing ':'")
        body = payload[colon + 1 :]
        parts = body.split(";")
        devices = []
        for p in parts:
            p = p.strip()
            if not p:
                continue
            fields = p.split(",")
            name = fields[0] if len(fields) > 0 else ""
            mode = fields[1] if len(fields) > 1 else ""
            dtype = fields[2] if len(fields) > 2 else ""
            val = fields[3] if len(fields) > 3 else ""

            # Now validate and convert device current type
            if mode == "S":
                mode = "SUBSCRIBER"
            elif mode == "P":
                mode = "PUBLISHER"
            else:
                logger.warning("Error, unknown device mode: " + str(mode))
                continue

            # Now validating and expanding device data type
            expanded_type = self.map_valid_type(dtype)
            if expanded_type is None:
                logger.warning("Error, unknown device data type: " + str(expanded_type))
                continue


            devices.append({"Name": name, "Mode": mode, "Type": expanded_type, "Value": val})
        return devices

    def _parse_compact_event(self, payload: str) -> Dict[str, str]:
        """
        Parse payload like:
          E:PirSensor,P,F,70.79#
        Returns dict {Name, Mode, Type, Value}
        """
        if payload.endswith("#"):
            payload = payload[:-1]
        if not payload.startswith("E:"):
            raise ValueError("not event")
        body = payload[2:]
        fields = body.split(",")
        name = fields[0] if len(fields) > 0 else ""
        mode = fields[1] if len(fields) > 1 else ""
        dtype = fields[2] if len(fields) > 2 else ""
        val = fields[3] if len(fields) > 3 else ""
        return {"Name": name, "Mode": mode, "Type": dtype, "Value": val}

    # -------------------------
    # Manifest handling (creates node_bridge if new)
    # -------------------------
    def _handle_manifest(self, addr: str, devices: List[Dict[str, Any]]):
        """
        Manifest-driven creation and update:
          - If node_bridge does not exist for addr, create it here.
          - Add publisher/subscriber devices (if not already present).
          - Update stored last-known values from manifest.
          - Publish manifest immediately via node_bridge (if possible).
        """
        logger.info("devices: " + str(devices) )
        with self._lock:
            first_time = False
            nb = self._node_bridges.get(addr)
            if nb is None:
                first_time = True
                # instantiate node_bridge for this XBee address
                node_name = addr.replace(":", "").upper()
                broker = self.configs.get("mqtt-host", "localhost")
                broker_port = int(self.configs.get("mqtt-port", 1883))
                keepalive = int(self.configs.get("keepalive", 60))
                sampling = int(self.configs.get("sampling", 6))
                mac_to_use = self._format_addr_as_mac(addr)
                logger.info("Creating node_bridge for %s -> node name %s mac=%s", addr, node_name, mac_to_use)
                try:
                    nb = node_bridge(node_name, broker, broker_port, keepalive, sampling, mac_addr=mac_to_use)
                    # acknowledge (connect to broker) before adding devices
                    nb.acknowledge()
                    # start_server will be called after devices are added
                except Exception:
                    logger.exception("Failed to create/acknowledge node_bridge for %s", addr)
                    nb = None

                if nb:
                    self._node_bridges[addr] = nb
                    self._device_states.setdefault(addr, {})
                    self._last_seen[addr] = time.time()

            # ensure device state dict exists
            state = self._device_states.setdefault(addr, {})

            # Process each device entry in manifest
            for dev in devices:
                try:
                    name = dev.get("Name")
                    mode = (dev.get("Mode") or "").upper()
                    dtype = dev.get("Type") or "STRING"
                    value = str(dev.get("Value", "")) if dev.get("Value", None) is not None else ""

                    if not name:
                        logger.warning("Manifest device without Name from %s: %s", addr, dev)
                        continue

                    # Update stored value (manifest provides initial/last-known)
                    state[name] = value

                    # If node_bridge exists, ensure devices are registered there
                    if nb:
                        # Publisher
                        if mode == "P" or mode == "PUBLISHER":
                            def make_value_cb(a=addr, n=name):
                                return lambda: self._get_device_value(a, n)
                            try:
                                nb.add_publisher_device(name, dtype, make_value_cb())
                                logger.info("Added publisher device %s on node %s", name, addr)
                            except Exception:
                                logger.debug("Publisher device %s may already exist on node %s", name, addr)
                        # Subscriber
                        elif mode == "S" or mode == "SUBSCRIBER":
                            def make_value_cb(a=addr, n=name):
                                return lambda: self._get_device_value(a, n)

                            def make_command_cb(a=addr, n=name):
                                def command_cb(payload_value: str):
                                    logger.info("Command callback called with " + str(payload_value))
                                    cmd_str = f"C:{n},{payload_value}#"
                                    try:
                                        sent = self.coordinator.sendMessage(a, cmd_str)
                                        with self._lock:
                                            self._device_states.setdefault(a, {})[n] = str(payload_value)
                                        if sent:
                                            logger.info("Relayed command to %s device=%s value=%s", a, n, payload_value)
                                        else:
                                            logger.warning("Failed to send command to %s device=%s", a, n)
                                    except Exception:
                                        logger.exception("Failed to send command to %s device=%s", a, n)
                                return command_cb

                            try:
                                nb.add_subscriber_device(name, dtype, make_value_cb(), make_command_cb())
                                logger.info("Added subscriber device %s on node %s", name, addr)
                            except Exception:
                                logger.debug("Subscriber device %s may already exist on node %s", name, addr)
                        else:
                            logger.warning("Unknown Mode '%s' for device %s from %s", mode, name, addr)
                except Exception:
                    logger.exception("Error processing manifest device %s from %s", dev, addr)

            # After processing manifest, start server if not already started and publish manifest immediately
            if nb and first_time:
                try:
                    # start_server may be idempotent in node_bridge implementation
                    nb.start_server()
                except Exception:
                    logger.exception("Failed to start_server for node %s", addr)

    # -------------------------
    # Event handling
    # -------------------------
    def _handle_event(self, addr: str, event: Dict[str, Any]):
        """
        Handle a single device event from a remote node:
          - Update local state
          - If node_bridge exists, forward event to node_bridge.send_event so it publishes to MQTT
          - If node_bridge does not exist yet, keep state; manifest will create the node_bridge later
        """
        name = event.get("Name")
        value = str(event.get("Value", ""))

        if not name:
            logger.warning("Event without Name from %s: %s", addr, event)
            return

        with self._lock:
            self._device_states.setdefault(addr, {})[name] = value

        nb = self._node_bridges.get(addr)
        if nb:
            try:
                nb.send_event(name, value)
                logger.info("Forwarded event from %s device=%s value=%s to node_bridge", addr, name, value)
            except Exception:
                logger.exception("Failed to forward event from %s device=%s", addr, name)
        else:
            # No node_bridge yet; manifest will create it. We keep the state updated so when manifest arrives
            # the publisher callback will return the latest value.
            logger.debug("Event for %s device=%s stored; node_bridge not yet created", addr, name)

    # -------------------------
    # Utilities
    # -------------------------
    def _get_device_value(self, addr: str, device_name: str) -> str:
        with self._lock:
            return self._device_states.get(addr, {}).get(device_name, "")

    def _format_addr_as_mac(self, addr: str) -> str:
        """
        Convert a 64-bit XBee address string into a colon-separated lower-case MAC-like string.
        """
        hexchars = ''.join(c for c in addr if c.isalnum())
        if len(hexchars) % 2 != 0:
            hexchars = '0' + hexchars
        pairs = [hexchars[i : i + 2] for i in range(0, len(hexchars), 2)]
        mac = ':'.join(p.lower() for p in pairs)
        return mac

    def publish_all_manifests(self):
        """
        Trigger immediate manifest publish for all active node_bridges.
        """
        with self._lock:
            for addr, nb in list(self._node_bridges.items()):
                try:
                    if hasattr(nb, "_build_and_send_payload_manifest"):
                        nb._build_and_send_payload_manifest()
                    elif hasattr(nb, "publish_manifest"):
                        nb.publish_manifest()
                    logger.info("Published manifest for node %s", addr)
                except Exception:
                    logger.exception("Failed to publish manifest for node %s", addr)

    def _cleaner_loop(self):
        """
        Background thread that removes node_bridges that have been inactive for INACTIVITY_TIMEOUT seconds.
        """
        logger.info("Cleaner thread started, timeout=%s", self.INACTIVITY_TIMEOUT)
        while not self._cleaner_stop.is_set():
            now = time.time()
            to_remove = []
            with self._lock:
                for addr, last in list(self._last_seen.items()):
                    if now - last > self.INACTIVITY_TIMEOUT:
                        to_remove.append(addr)
                for addr in to_remove:
                    try:
                        nb = self._node_bridges.pop(addr, None)
                        if nb:
                            nb.disable()
                            logger.info("Removed inactive node_bridge for %s", addr)
                        self._device_states.pop(addr, None)
                        self._last_seen.pop(addr, None)
                    except Exception:
                        logger.exception("Error removing inactive node %s", addr)
            # sleep a short while
            self._cleaner_stop.wait(5.0)
        logger.info("Cleaner thread exiting")


