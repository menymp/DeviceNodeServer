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
import queue
from typing import Callable, Optional, List

try:
    from digi.xbee.devices import XBeeDevice, RemoteXBeeDevice, XBee64BitAddress
except Exception as e:
    raise RuntimeError("digi.xbee library required: install digi-xbee in your image") from e

logger = logging.getLogger("XbeeNetCoordinator")


class XbeeNetCoordinator:
    def __init__(self, discovery_time: int = 30, sender_workers: int = 2):
        self._device: Optional[XBeeDevice] = None
        self._port = None
        self._baud = 9600
        self._message_cb: Optional[Callable[[str, str], None]] = None
        self._sync_cb: Optional[Callable[[List[str]], None]] = None
        self._discovery_time = discovery_time
        self._running = False
        self._lock = threading.RLock()
        self._opened = False

        # Async send queue and worker(s)
        self._send_queue: "queue.Queue[tuple[str,str]]" = queue.Queue()
        self._sender_threads: List[threading.Thread] = []
        self._sender_stop = threading.Event()
        self._sender_worker_count = sender_workers

    def init(self, comm_port_path: str, baud_rate: int,
             message_received_callback: Callable[[str, str], None] = None,
             sync_devices_callback: Callable[[List[str]], None] = None):
        self._port = comm_port_path
        self._baud = int(baud_rate)
        self._message_cb = message_received_callback
        self._sync_cb = sync_devices_callback
        logger.info("Coordinator configured comm=%s baud=%s discovery=%s",
                    self._port, self._baud, self._discovery_time)

    def start(self):
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

            # register receive callback
            def _on_data_receive(xbee_message):
                try:
                    remote = xbee_message.remote_device
                    addr_obj = remote.get_64bit_addr()
                    addr_str = str(addr_obj)
                    data = xbee_message.data.decode(errors="ignore")
                    logger.debug("RX from %s -> %s", addr_str, data)
                    if self._message_cb:
                        self._message_cb(addr_str, data)
                except Exception:
                    logger.exception("Error in data receive callback")

            self._device.add_data_received_callback(_on_data_receive)

            # start sender workers
            self._sender_stop.clear()
            for i in range(self._sender_worker_count):
                t = threading.Thread(target=self._sender_worker, daemon=True, name=f"xbee-sender-{i}")
                t.start()
                self._sender_threads.append(t)

            self._running = True
            logger.info("Coordinator started and listening on %s", self._port)

    def _sender_worker(self):
        logger.info("XBee sender worker started")
        while not self._sender_stop.is_set():
            try:
                addr64_str, payload = self._send_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                logger.debug("Dequeued send to %s payload=%s ts=%s", addr64_str, payload, time.time())
                # perform send with small retry/backoff
                success = False
                attempts = 0
                while not success and attempts < 3:
                    attempts += 1
                    success = self._perform_send(addr64_str, payload)
                    if not success:
                        logger.warning("Send attempt %d failed for %s, retrying", attempts, addr64_str)
                        time.sleep(0.05 * attempts)  # small backoff
                if not success:
                    logger.error("Failed to send payload to %s after %d attempts", addr64_str, attempts)
                else:
                    logger.debug("Send completed to %s payload=%s ts=%s", addr64_str, payload, time.time())
                # small inter-frame delay to avoid radio saturation
                time.sleep(0.02)
            except Exception:
                logger.exception("Exception while sending payload to %s", addr64_str)
            finally:
                try:
                    self._send_queue.task_done()
                except Exception:
                    pass
        logger.info("XBee sender worker exiting")

    def _perform_send(self, addr64_str: str, payload: str) -> bool:
        if not self._opened or not self._device:
            logger.warning("Device not open, cannot send")
            return False
        try:
            hexchars = ''.join(c for c in addr64_str if c.isalnum())
            if len(hexchars) % 2 != 0:
                hexchars = '0' + hexchars
            addr_obj = XBee64BitAddress.from_hex_string(hexchars)
            remote = RemoteXBeeDevice(self._device, addr_obj)
            self._device.send_data(remote, payload)
            return True
        except Exception:
            logger.exception("Failed to send to %s payload=%s", addr64_str, payload)
            return False

    def sendMessage(self, addr64_str: str, payload: str) -> bool:
        try:
            self._send_queue.put_nowait((addr64_str, payload))
            logger.debug("Enqueued send to %s payload=%s queue_size=%d", addr64_str, payload, self._send_queue.qsize())
            return True
        except Exception:
            logger.exception("Failed to enqueue send to %s", addr64_str)
            return False

    def sendMessageSync(self, addr64_str: str, payload: str, timeout: float = 5.0) -> bool:
        if not self.sendMessage(addr64_str, payload):
            return False
        start = time.time()
        while time.time() - start < timeout:
            if self._send_queue.empty():
                return True
            time.sleep(0.01)
        logger.warning("sendMessageSync timeout for %s", addr64_str)
        return False

    def stop(self):
        with self._lock:
            try:
                self._sender_stop.set()
                for t in self._sender_threads:
                    if t.is_alive():
                        t.join(timeout=1.0)
            except Exception:
                logger.exception("Error stopping sender workers")

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
