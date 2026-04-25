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

import json
import threading
from typing import Dict, Any, List, Optional
import logging
import os

from XbeeNetCoordinator import XbeeNetCoordinator
from node_bridge import node_bridge

logging.basicConfig(level=os.environ.get("WORKER_LOG_LEVEL", "INFO"))
logger = logging.getLogger("XbeeNetworkController")


class XbeeNetworkController:
    """
    Controller that maps each discovered XBee remote device to a node_bridge instance.
    Node_bridge instances always receive a mac_addr derived from the XBee address.
    """

    def __init__(self, configs: Dict[str, Any]):
        """
        configs expected keys:
          - mqtt-host
          - mqtt-port
          - name (controller name prefix)
          - comm-port-path
          - com-baud-rate
          - discovery-time (optional)
        """
        self.configs = configs
        discovery_time = configs.get("discovery-time", 120)
        self.coordinator = XbeeNetCoordinator(discovery_time=discovery_time)

        # Map remote address (string) -> node_bridge instance
        self._node_bridges: Dict[str, node_bridge] = {}

        # Map remote address -> device state dict: deviceName -> lastValue (strings)
        self._device_states: Dict[str, Dict[str, str]] = {}

        # Lock to protect maps
        self._lock = threading.RLock()

        logger.info(
            "XbeeNetworkController initialized: mqtt=%s:%s comm=%s@%s discovery=%s",
            configs.get("mqtt-host"),
            configs.get("mqtt-port"),
            configs.get("comm-port-path"),
            configs.get("com-baud-rate"),
            discovery_time,
        )

    # -------------------------
    # Lifecycle
    # -------------------------
    def start(self):
        """
        Initialize coordinator and start background processing.
        Node bridges are created on discovery or on first message.
        """
        logger.info("Starting XbeeNetworkController")
        self.coordinator.init(
            self.configs["comm-port-path"],
            self.configs["com-baud-rate"],
            message_received_callback=self._message_received_callback,
            sync_devices_callback=self._on_devices_discovered
        )
        # Coordinator worker will run discovery and message handling
        self.coordinator.start()
        logger.info("Coordinator started")

    def stop(self):
        """
        Stop coordinator and disable all node bridges.
        """
        logger.info("Stopping XbeeNetworkController")
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

        # Stop coordinator
        try:
            self.coordinator.stop()
            self.coordinator.close()
            logger.info("Coordinator stopped and closed")
        except Exception:
            logger.exception("Error stopping coordinator")

    # -------------------------
    # Coordinator callbacks
    # -------------------------
    def _on_devices_discovered(self, device_addresses: List[str]):
        """
        Called by coordinator after discovery completes with a list of address strings.
        Ensure node_bridge instances exist for each discovered device.
        """
        logger.info("Discovery callback: %s", device_addresses)
        for addr in device_addresses:
            derived_mac = self._format_addr_as_mac(addr)
            # Always create node_bridge now with derived mac (manifest MACs are ignored)
            self._ensure_node_bridge_for(addr, mac_addr=derived_mac)

    def _message_received_callback(self, address64bit: str, data: str):
        """
        Called by Xbee coordinator when a frame arrives from a remote device.
        Expects JSON payloads in one of the forms:
          - Manifest: {"Devices":[{...}, ...]}
          - Event: {"Name": "...", "Mode":"PUBLISHER", "Type":"STRING", "Value":"..."}
        Manifest MAC fields are ignored; MAC always comes from XBee address.
        """
        addr = str(address64bit)
        logger.debug("Message received from %s: %s", addr, data)

        # Ensure node_bridge exists for this address (use derived mac)
        nb = self._ensure_node_bridge_for(addr, mac_addr=self._format_addr_as_mac(addr))

        # Parse JSON
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON from %s: %s", addr, data)
            return

        # Manifest handling
        if isinstance(payload, dict) and "Devices" in payload and isinstance(payload["Devices"], list):
            logger.info("Manifest received from %s with %d devices", addr, len(payload["Devices"]))
            # Ignore any MacAddress in manifest; use XBee-derived MAC only
            self._handle_manifest(addr, payload["Devices"], nb)
            return

        # Event handling (single device object)
        if isinstance(payload, dict) and "Name" in payload and "Value" in payload:
            logger.info(
                "Event received from %s device=%s value=%s", addr, payload.get("Name"), payload.get("Value")
            )
            self._handle_event(addr, payload, nb)
            return

        logger.debug("Unhandled JSON message from %s: %s", addr, payload)

    # -------------------------
    # Node bridge management
    # -------------------------
    def _ensure_node_bridge_for(self, addr: str, mac_addr: Optional[str] = None) -> node_bridge:
        """
        Ensure a node_bridge instance exists for the given XBee 64-bit address.
        If not present, create, acknowledge, and start it.
        mac_addr is required and must be derived from the XBee address (we enforce that).
        """
        with self._lock:
            if addr in self._node_bridges:
                return self._node_bridges[addr]

            # Create node_bridge instance
            node_name = addr.replace(":", "").upper()  # normalize name (no colons)
            broker = self.configs.get("mqtt-host", "localhost")
            broker_port = int(self.configs.get("mqtt-port", 1883))
            keepalive = int(self.configs.get("keepalive", 60))
            sampling = int(self.configs.get("sampling", 6))

            # If no mac provided, derive one from the XBee address
            mac_to_use = mac_addr if mac_addr else self._format_addr_as_mac(addr)

            logger.info("Creating node_bridge for %s -> node name %s mac=%s", addr, node_name, mac_to_use)
            try:
                nb = node_bridge(node_name, broker, broker_port, keepalive, sampling, mac_addr=mac_to_use)
                # Immediately acknowledge/register with broker
                nb.acknowledge()
                # Start server loop for this node_bridge (non-blocking in node_bridge implementation)
                nb.start_server()
            except Exception:
                logger.exception("Failed to create/start node_bridge for %s", addr)
                raise

            # initialize device state store for this node
            self._device_states[addr] = {}

            # store and return
            self._node_bridges[addr] = nb
            logger.info("node_bridge created for %s (mac=%s)", addr, mac_to_use)
            return nb

    # -------------------------
    # Manifest / Event handling
    # -------------------------
    def _handle_manifest(self, addr: str, devices: List[Dict[str, Any]], nb: node_bridge):
        """
        For each device in the manifest:
          - If PUBLISHER: add a publisher device to node_bridge with a value callback that reads from local state.
          - If SUBSCRIBER: add a subscriber device to node_bridge with a command callback that sends commands to the XBee node.
        """
        with self._lock:
            state = self._device_states.setdefault(addr, {})

            for dev in devices:
                try:
                    name = dev.get("Name")
                    mode = dev.get("Mode", "").upper()
                    dtype = dev.get("Type", "STRING")
                    value = str(dev.get("Value", "")) if dev.get("Value", None) is not None else ""

                    if not name:
                        logger.warning("Manifest device without Name from %s: %s", addr, dev)
                        continue

                    # store initial value
                    state[name] = value

                    # Publisher: add publisher device if not exists
                    if mode == "PUBLISHER":
                        def make_value_cb(a=addr, n=name):
                            return lambda: self._get_device_value(a, n)
                        try:
                            nb.add_publisher_device(name, dtype, make_value_cb())
                            logger.info("Added publisher device %s on node %s", name, addr)
                        except Exception:
                            logger.debug("Publisher device %s may already exist on node %s", name, addr)

                    # Subscriber: add subscriber device if not exists
                    elif mode == "SUBSCRIBER":
                        def make_value_cb(a=addr, n=name):
                            return lambda: self._get_device_value(a, n)

                        def make_command_cb(a=addr, n=name):
                            def command_cb(payload_value: str):
                                cmd = {"Device": n, "Value": str(payload_value)}
                                try:
                                    self._send_command_to_xbee(a, cmd)
                                    with self._lock:
                                        self._device_states.setdefault(a, {})[n] = str(payload_value)
                                    logger.info("Relayed command to %s device=%s value=%s", a, n, payload_value)
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

            # After processing manifest, publish the node manifest via node_bridge if available
            try:
                nb.publish_manifest()
                logger.debug("Published manifest for node %s", addr)
            except Exception:
                logger.exception("Failed to publish manifest for node %s", addr)

    def _handle_event(self, addr: str, event: Dict[str, Any], nb: node_bridge):
        """
        Handle a single device event from a remote node:
          - Update local state
          - Forward event to node_bridge.send_event so it publishes to MQTT
        """
        name = event.get("Name")
        value = str(event.get("Value", ""))

        if not name:
            logger.warning("Event without Name from %s: %s", addr, event)
            return

        with self._lock:
            self._device_states.setdefault(addr, {})[name] = value

        try:
            nb.send_event(name, value)
            logger.info("Forwarded event from %s device=%s value=%s to node_bridge", addr, name, value)
        except Exception:
            logger.exception("Failed to forward event from %s device=%s", addr, name)

    # -------------------------
    # Command sending
    # -------------------------
    def _send_command_to_xbee(self, addr: str, cmd_obj: Dict[str, Any]):
        """
        Send a command JSON to the XBee node via coordinator.
        The node firmware is expected to accept JSON like:
          {"Device":"WaterPump", "Value":"OFF"}
        """
        try:
            payload = json.dumps(cmd_obj)
            sent = self.coordinator.sendMessage(addr, payload)
            if not sent:
                logger.warning("Coordinator queue full or send failed for %s payload=%s", addr, payload)
                raise RuntimeError("sendMessage failed")
            logger.debug("Command queued to %s payload=%s", addr, payload)
        except Exception:
            logger.exception("Error sending command to %s payload=%s", addr, cmd_obj)
            raise

    # -------------------------
    # Utilities
    # -------------------------
    def _get_device_value(self, addr: str, device_name: str) -> str:
        with self._lock:
            return self._device_states.get(addr, {}).get(device_name, "")

    def _format_addr_as_mac(self, addr: str) -> str:
        """
        Convert a 64-bit XBee address string (e.g. '0013A20040XXXXXX' or '00:13:A2:00:40:XX:XX:XX')
        into a colon-separated lower-case MAC-like string '00:13:a2:00:40:xx:xx:xx'.
        """
        hexchars = ''.join(c for c in addr if c.isalnum())
        if len(hexchars) % 2 != 0:
            hexchars = '0' + hexchars
        pairs = [hexchars[i : i + 2] for i in range(0, len(hexchars), 2)]
        mac = ':'.join(p.lower() for p in pairs)
        return mac

    def publish_all_manifests(self):
        with self._lock:
            for addr, nb in self._node_bridges.items():
                try:
                    nb.publish_manifest()
                    logger.info("Published manifest for node %s", addr)
                except Exception:
                    logger.exception("Failed to publish manifest for node %s", addr)

