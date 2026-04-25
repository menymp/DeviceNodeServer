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

# xbeeNetCoordinator.py
# Drop-in replacement XBee coordinator with non-blocking request/response,
# background discovery, and integrated logging via the shared `logger` util.
#
# Public API (same as previous):
#   - init(port_path, baud_rate, message_received_callback=None, sync_devices_callback=None)
#   - start()
#   - stop()
#   - close()
#   - sendMessage(address64String, data) -> bool
#
# Callbacks:
#   - message_received_callback(address, data)
#   - sync_devices_callback(list_of_address_strings)
#
# Dependencies: digi-xbee (digi.xbee.*), standard Python libs, and a `logger` util
# that exposes `logger.info`, `logger.debug`, `logger.warning`, `logger.exception`.
#
# Paste this file into your project and import XbeeNetMqttCoordinator where needed.

import time
import threading
import queue
import logging
import os
from typing import Optional, Callable, Tuple, List

from digi.xbee.models.status import NetworkDiscoveryStatus
from digi.xbee.devices import XBeeDevice, RemoteXBeeDevice

# Use the project's shared logger util (must expose logger.info/debug/warning/exception)
# Adjust import path if your logger util lives elsewhere.

logging.basicConfig(level=os.environ.get("WORKER_LOG_LEVEL", "INFO"))
logger = logging.getLogger("XbeeNetCoordinator")

class XbeeNetCoordinator:
    """
    Robust XBee coordinator for coordinator <-> nodes communication.

    - Non-blocking request/response with retries and timeouts.
    - Background discovery that does not block data flow.
    - Concurrent send/receive handling.
    - Uses the project's `logger` util for all logs.
    """

    def __init__(
        self,
        discovery_time: int = 120,
        max_request_size: int = 10,
        request_timeout: float = 1.0,
        max_retries: int = 2,
    ):
        # configuration
        self.discovery_time = discovery_time
        self.max_request_size = max_request_size
        self.request_timeout = request_timeout  # seconds to wait for a response per attempt
        self.max_retries = max_retries

        # xbee runtime
        self.coordinatorDevice: Optional[XBeeDevice] = None
        self.xbee_network = None

        # device lists
        self.networkDevices: List = []
        self.remoteDevices: List[RemoteXBeeDevice] = []
        self.remoteStrAddresses: List[str] = []

        # threading and queues
        self._stop_event = threading.Event()
        self._search_event = threading.Event()
        self._incoming_requests = queue.Queue(maxsize=max_request_size)
        self._worker_thread: Optional[threading.Thread] = None
        self._discovery_timer: Optional[threading.Timer] = None

        # request/response coordination
        self._pending_lock = threading.Lock()
        # seq -> {"event": Event, "response": (addr, data), "attempts": int, "address": str}
        self._pending = {}

        # callbacks
        self._message_received_callback: Optional[Callable[[str, str], None]] = None
        self._sync_devices_callback: Optional[Callable[[List[str]], None]] = None

        # sequence generator
        self._seq_lock = threading.Lock()
        self._seq = 0

        logger.info("XbeeNetMqttCoordinator initialized (discovery_time=%s, request_timeout=%s, max_retries=%s)",
                    discovery_time, request_timeout, max_retries)

    # -------------------------
    # Public lifecycle methods
    # -------------------------
    def init(self, port_path: str, baud_rate: int,
             message_received_callback: Optional[Callable[[str, str], None]] = None,
             sync_devices_callback: Optional[Callable[[List[str]], None]] = None):
        """
        Open coordinator device and configure network callbacks.
        """
        self._message_received_callback = message_received_callback
        self._sync_devices_callback = sync_devices_callback

        logger.info("Opening XBee coordinator on port %s @ %d", port_path, baud_rate)
        self.coordinatorDevice = XBeeDevice(port_path, baud_rate)
        self.coordinatorDevice.open()

        # register data receive callback
        self.coordinatorDevice.add_data_received_callback(self._message_arrived_callback)

        # init network object and discovery callbacks
        self._init_xbee_network()
        logger.info("Coordinator initialized and callbacks registered")

    def start(self):
        """
        Start background worker and schedule discovery.
        """
        if self._worker_thread and self._worker_thread.is_alive():
            logger.warning("start() called but worker already running")
            return
        logger.info("Starting coordinator worker and scheduling discovery")
        self._stop_event.clear()
        self._search_event.set()
        self._worker_thread = threading.Thread(target=self._worker_loop, name="XbeeCoordinatorWorker", daemon=True)
        self._worker_thread.start()
        self._schedule_discovery()

    def stop(self):
        """
        Stop background worker and discovery scheduling.
        """
        logger.info("Stopping coordinator worker and discovery")
        self._stop_event.set()
        self._search_event.clear()
        if self._discovery_timer:
            try:
                self._discovery_timer.cancel()
            except Exception:
                logger.exception("Error cancelling discovery timer")
            self._discovery_timer = None

        # wake pending requests so callers don't hang
        with self._pending_lock:
            for seq, info in list(self._pending.items()):
                try:
                    info["event"].set()
                except Exception:
                    logger.exception("Error setting pending event for seq %s", seq)
            self._pending.clear()

    def close(self):
        """
        Stop and close the XBee device.
        """
        logger.info("Closing coordinator")
        self.stop()
        if self.coordinatorDevice is not None and self.coordinatorDevice.is_open():
            try:
                self.coordinatorDevice.close()
                logger.info("Coordinator device closed")
            except Exception:
                logger.exception("Error closing coordinator device")

    # -------------------------
    # Sending and requests
    # -------------------------
    def sendMessage(self, address64String: str, data: str) -> bool:
        """
        Queue a message to be sent to a remote device. Nonblocking.
        Returns True if queued, False if queue full.
        """
        msg = {"address": address64String, "data": data}
        try:
            self._incoming_requests.put_nowait(msg)
            logger.debug("Queued outgoing message to %s", address64String)
            return True
        except queue.Full:
            logger.warning("Outgoing queue full, dropping message to %s", address64String)
            return False

    def _send_coordinator_message(self, address64String: str, data: str) -> bool:
        """
        Send without waiting. Returns True if send initiated.
        """
        exists, remoteDevice = self.deviceExists(address64String)
        if not exists:
            logger.warning("Attempt to send to unknown device %s", address64String)
            return False
        try:
            # async send so we don't block on serial
            self.coordinatorDevice.send_data_async(remoteDevice, data)
            logger.debug("send_data_async initiated to %s payload=%s", address64String, data)
            return True
        except Exception:
            logger.exception("send_data_async failed for %s", address64String)
            return False

    def _start_request_response(self, address: str, message: str) -> Tuple[bool, Optional[Tuple[str, str]]]:
        """
        Nonblocking request/response with retries.
        Returns (success, (addr, data) or None)
        """
        seq = self._next_seq()
        event = threading.Event()
        with self._pending_lock:
            self._pending[seq] = {"event": event, "response": None, "attempts": 0, "address": address}

        logger.debug("Starting request/response seq=%s to %s message=%s", seq, address, message)

        for attempt in range(1, self.max_retries + 2):  # attempts = max_retries + initial
            with self._pending_lock:
                self._pending[seq]["attempts"] = attempt

            # embed seq in message so remote can echo it back if you implement that
            payload = f"{seq}:{message}"
            sent = self._send_coordinator_message(address, payload)
            if not sent:
                logger.warning("Failed to send seq=%s to %s on attempt %d", seq, address, attempt)
                time.sleep(0.05)
                continue

            # wait for response or timeout
            got = event.wait(self.request_timeout)
            if got:
                with self._pending_lock:
                    resp = self._pending.pop(seq, {}).get("response")
                logger.debug("Received response for seq=%s from %s", seq, address)
                return True, resp
            else:
                logger.debug("No response for seq=%s attempt=%d", seq, attempt)
                # small backoff before retry
                time.sleep(0.05 + 0.05 * attempt)

        # exhausted attempts
        with self._pending_lock:
            self._pending.pop(seq, None)
        logger.warning("Exhausted attempts for seq=%s to %s", seq, address)
        return False, None

    # -------------------------
    # Worker loop and state update
    # -------------------------
    def _worker_loop(self):
        """
        Main background loop: handle discovery triggers, queued requests, and periodic updates.
        """
        logger.info("Coordinator worker started")
        state_index = 0
        while not self._stop_event.is_set():
            # discovery requested
            if self._search_event.is_set():
                try:
                    self._discovery_devices()
                except Exception:
                    logger.exception("Discovery failed")
                finally:
                    self._search_event.clear()

            # process queued outgoing requests
            try:
                msg = self._incoming_requests.get_nowait()
            except queue.Empty:
                msg = None

            if msg:
                addr = msg["address"]
                data = msg["data"]
                logger.debug("Processing queued message to %s", addr)
                success, resp = self._start_request_response(addr, data)
                if not success:
                    logger.warning("Request to %s failed after retries", addr)
                else:
                    # call user callback with response
                    if self._message_received_callback:
                        try:
                            self._message_received_callback(resp[0], resp[1])
                        except Exception:
                            logger.exception("message_received_callback failed")
            else:
                # no queued requests, perform periodic state poll if devices exist
                if self.remoteStrAddresses:
                    addr = self.remoteStrAddresses[state_index % len(self.remoteStrAddresses)]
                    logger.debug("Polling UPDATE for %s", addr)
                    try:
                        success, resp = self._start_request_response(addr, "UPDATE")
                        if success and self._message_received_callback:
                            try:
                                self._message_received_callback(resp[0], resp[1])
                            except Exception:
                                logger.exception("message_received_callback failed")
                    except Exception:
                        logger.exception("Error during UPDATE for %s", addr)
                    state_index = (state_index + 1) % max(1, len(self.remoteStrAddresses))
                else:
                    # nothing to do, sleep a bit
                    time.sleep(0.1)

        logger.info("Coordinator worker stopped")

    # -------------------------
    # Message receive handling
    # -------------------------
    def _message_arrived_callback(self, xbee_message):
        """
        Called by library when a frame arrives. Matches responses to pending requests if seq present.
        """
        try:
            address = str(xbee_message.remote_device.get_64bit_addr())
            raw = xbee_message.data.decode("utf8", errors="ignore")
            logger.debug("Frame arrived from %s raw=%s", address, raw)

            # Expecting payload format "seq:payload" if sent by _start_request_response
            seq = None
            payload = raw
            if ":" in raw:
                maybe_seq, rest = raw.split(":", 1)
                if maybe_seq.isdigit():
                    seq = int(maybe_seq)
                    payload = rest

            if seq is not None:
                with self._pending_lock:
                    info = self._pending.get(seq)
                    if info:
                        info["response"] = (address, payload)
                        info["event"].set()
                        logger.debug("Matched incoming frame to pending seq=%s from %s", seq, address)
                        return  # handled as response

            # otherwise treat as unsolicited message and call callback
            logger.info("Unsolicited message from %s payload=%s", address, payload)
            if self._message_received_callback:
                try:
                    self._message_received_callback(address, payload)
                except Exception:
                    logger.exception("message_received_callback failed")
        except Exception:
            logger.exception("Error in _message_arrived_callback")

    # -------------------------
    # Discovery and network init
    # -------------------------
    def _init_xbee_network(self):
        """
        Configure the XBee network object and discovery callbacks.
        """
        self.xbee_network = self.coordinatorDevice.get_network()

        def on_device_discovered(remote):
            logger.info("Device discovered: %s", remote)

        def on_discovery_finished(status):
            if status == NetworkDiscoveryStatus.SUCCESS:
                logger.info("Discovery finished successfully")
            else:
                desc = getattr(status, "description", str(status))
                logger.warning("Discovery finished with status: %s", desc)

        self.xbee_network.add_device_discovered_callback(on_device_discovered)
        self.xbee_network.add_discovery_process_finished_callback(on_discovery_finished)
        logger.debug("XBee network callbacks registered")

    def _schedule_discovery(self):
        """
        Schedule periodic discovery using a Timer. Cancels previous timer if present.
        """
        if self._discovery_timer:
            try:
                self._discovery_timer.cancel()
            except Exception:
                logger.exception("Error cancelling previous discovery timer")
        if self._stop_event.is_set():
            return
        logger.debug("Scheduling discovery in %s seconds", self.discovery_time)
        self._discovery_timer = threading.Timer(self.discovery_time, self._set_search_flag)
        self._discovery_timer.daemon = True
        self._discovery_timer.start()

    def _set_search_flag(self):
        logger.debug("Discovery flag set")
        self._search_event.set()
        # reschedule next discovery
        self._schedule_discovery()

    def _discovery_devices(self):
        """
        Start discovery and update remote device lists when finished.
        Non-blocking to the rest of the system (runs in worker thread).
        """
        logger.info("Starting XBee discovery")
        self.xbee_network.set_discovery_timeout(25)
        self.xbee_network.clear()
        try:
            self.xbee_network.start_discovery_process()
            logger.info("Discovering remote XBee devices...")
            # wait for discovery to finish but allow stop_event to interrupt
            while self.xbee_network.is_discovery_running():
                if self._stop_event.is_set():
                    try:
                        self.xbee_network.stop_discovery_process()
                    except Exception:
                        logger.exception("Error stopping discovery process")
                    return
                time.sleep(0.1)
        except Exception:
            logger.exception("Exception while running discovery process")
            return

        # update device lists
        try:
            self.networkDevices = self.xbee_network.get_devices()
            for device in self.networkDevices:
                addr_str = str(device.get_64bit_addr())
                if addr_str in self.remoteStrAddresses:
                    continue
                try:
                    remote = RemoteXBeeDevice(self.coordinatorDevice, device.get_64bit_addr())
                    self.remoteDevices.append(remote)
                    self.remoteStrAddresses.append(addr_str)
                    logger.info("Added remote device %s", addr_str)
                except Exception:
                    logger.exception("Failed to create RemoteXBeeDevice for %s", addr_str)
        except Exception:
            logger.exception("Failed to update network devices list after discovery")

        logger.info("Available network devices: %s", self.remoteStrAddresses)
        if self._sync_devices_callback:
            try:
                self._sync_devices_callback(self.remoteStrAddresses)
            except Exception:
                logger.exception("sync_devices_callback failed")

    # -------------------------
    # Utilities
    # -------------------------
    def deviceExists(self, address64String: str) -> Tuple[bool, Optional[RemoteXBeeDevice]]:
        """
        Return (found, RemoteXBeeDevice or None).
        """
        for dev in self.remoteDevices:
            try:
                if str(dev.get_64bit_addr()) == address64String:
                    return True, dev
            except Exception:
                continue
        return False, None

    def _next_seq(self) -> int:
        with self._seq_lock:
            self._seq += 1
            # wrap to avoid unbounded growth
            if self._seq > 0x7FFFFFFF:
                self._seq = 1
            return self._seq
