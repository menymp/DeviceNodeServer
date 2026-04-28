'''
xbee coordinator class that allow the discovery and message backward and forward processing
menymp
Nov 2023

OK: Since the discovery process would take place it will interrupt the process for a while, a better approach in the future could be split the process
into two devices for search and for message relay
OK: Devices seems to interfer with each other, a sync operation with an expected return data should be implemented for each device
or maybe seek for the root cause


Apr 2026
An rework was done and was included since api can still work as a full duplex while discovering devices.
'''

# XbeeNetCoordinator.py
# Abstraction around digi.xbee XBeeDevice for serial comms.
# Provides: init(comm_port_path, baud_rate, message_received_callback),
# start(), stop(), sendMessage(addr64_str, payload_str)
import logging
import threading
import time
from typing import Callable, Optional, List

try:
    from digi.xbee.devices import XBeeDevice, RemoteXBeeDevice, XBee64BitAddress
except Exception as e:
    raise RuntimeError("digi.xbee library required: install digi-xbee in your image") from e

logger = logging.getLogger("XbeeNetCoordinator")


class XbeeNetCoordinator:
    """
    Coordinator that manages the local XBee serial device.
    Callbacks:
      - message_received_callback(address64_str, payload_str)
      - sync_devices_callback(list_of_address64_str)  (kept for compatibility but not used)
    """

    def __init__(self, discovery_time: int = 30):
        self._device: Optional[XBeeDevice] = None
        self._port = None
        self._baud = 9600
        self._message_cb: Optional[Callable[[str, str], None]] = None
        self._sync_cb: Optional[Callable[[List[str]], None]] = None
        self._discovery_time = discovery_time
        self._running = False
        self._lock = threading.RLock()
        self._opened = False

    def init(self, comm_port_path: str, baud_rate: int,
             message_received_callback: Callable[[str, str], None] = None,
             sync_devices_callback: Callable[[List[str]], None] = None):
        """
        Configure the coordinator. Does not open the serial port yet.
        """
        self._port = comm_port_path
        self._baud = int(baud_rate)
        self._message_cb = message_received_callback
        self._sync_cb = sync_devices_callback
        logger.info("Coordinator configured comm=%s baud=%s discovery=%s",
                    self._port, self._baud, self._discovery_time)

    def start(self):
        """
        Open the XBee device and register receive callback.
        No discovery procedure is required for this deployment; devices will send manifests/events.
        """
        with self._lock:
            if self._running:
                return
            if not self._port:
                raise RuntimeError("comm port not configured")
            self._device = XBeeDevice(self._port, self._baud)
            try:
                self._device.open()
                self._opened = True
            except Exception:
                logger.exception("Failed to open XBee device on %s", self._port)
                raise

            # register callback
            def _on_data_receive(xbee_message):
                try:
                    remote = xbee_message.remote_device
                    addr_obj = remote.get_64bit_addr()
                    addr_str = str(addr_obj)
                    data = xbee_message.data.decode(errors="ignore")
                    logger.debug("RX from %s -> %s", addr_str, data)
                    if self._message_cb:
                        # deliver raw payload string as-is
                        self._message_cb(addr_str, data)
                except Exception:
                    logger.exception("Error in data receive callback")

            self._device.add_data_received_callback(_on_data_receive)
            self._running = True
            logger.info("Coordinator started and listening on %s", self._port)

    def sendMessage(self, addr64_str: str, payload: str) -> bool:
        """
        Send payload (string) to remote device identified by 64-bit address string.
        Returns True on success, False otherwise.
        """
        with self._lock:
            if not self._opened or not self._device:
                logger.warning("Device not open, cannot send")
                return False
            try:
                net = self._device.get_network()
                # try to discover the remote device object quickly
                try:
                    net.set_discovery_timeout(2)  #Check if this could be a good approach OR to hold a device list to use
                    remote = net.discover_device(addr64_str)
                except Exception:
                    remote = None

                if remote is None:
                    # fallback: create RemoteXBeeDevice from address string
                    # Accept formats like '0013A20040XXXXXX' or '00:13:A2:00:40:XX:XX:XX'
                    hexchars = ''.join(c for c in addr64_str if c.isalnum())
                    if len(hexchars) % 2 != 0:
                        hexchars = '0' + hexchars
                    addr_obj = XBee64BitAddress.from_hex_string(hexchars)
                    remote = RemoteXBeeDevice(self._device, addr_obj)

                # send data (string)
                self._device.send_data(remote, payload)
                logger.debug("Queued send to %s payload=%s", addr64_str, payload)
                return True
            except Exception:
                logger.exception("Failed to send to %s payload=%s", addr64_str, payload)
                return False

    def stop(self):
        """
        Stop coordinator and close device.
        """
        with self._lock:
            if not self._opened or not self._device:
                return
            try:
                self._device.close()
                logger.info("Coordinator device closed")
            except Exception:
                logger.exception("Error closing device")
            finally:
                self._opened = False
                self._running = False


