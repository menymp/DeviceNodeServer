#!/usr/bin/env python3
"""
picamclient.py

Captures JPEG frames from Raspberry Pi Camera v1 with opencv (via Picamera2) 
and sends them to a TCP ingest server using the ESP32 framing/protocol.

[4 bytes BE header_len][header_json bytes][4 bytes BE image_len][jpeg bytes]
"""

import io
import json
import socket
import struct
import time
import os
import sys
import signal
import logging
from typing import Optional

try:
    import cv2
except Exception:
    cv2 = None

try:
    from picamera2 import Picamera2
except Exception:
    Picamera2 = None

try:
    import netifaces
except Exception:
    netifaces = None

# Config via env
SERVER_IP = os.environ.get("INGEST_SERVER_IP", "192.168.1.100")
SERVER_PORT = int(os.environ.get("INGEST_SERVER_PORT", "8072"))
CAMERA_NAME = os.environ.get("CAMERA_NAME", "MenyPiCam1")
CAMERA_TYPE = os.environ.get("CAMERA_TYPE", "1")
CAPTURE_INTERVAL_MS = int(os.environ.get("CAPTURE_INTERVAL_MS", "1000"))
NET_INTERFACE = os.environ.get("NET_INTERFACE", "eth0")
RESOLUTION = os.environ.get("RESOLUTION", "800x600")
JPEG_QUALITY = int(os.environ.get("JPEG_QUALITY", "85"))

LOG = logging.getLogger("pi_cam_cv")
LOG.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
LOG.addHandler(handler)

running = True
sock: Optional[socket.socket] = None

def get_mac_no_colon(interface: str = NET_INTERFACE) -> str:
    if netifaces:
        try:
            addrs = netifaces.ifaddresses(interface)
            mac = addrs.get(netifaces.AF_LINK, [{}])[0].get('addr')
            if mac:
                return mac.replace(":", "").replace("-", "").upper()
        except Exception:
            pass
    try:
        with open(f"/sys/class/net/{interface}/address", "r") as f:
            mac = f.read().strip()
            if mac:
                return mac.replace(":", "").replace("-", "").upper()
    except Exception:
        pass
    import uuid
    return f"{uuid.getnode():012X}"

def get_ip_addr(interface: str = NET_INTERFACE) -> str:
    if netifaces:
        try:
            addrs = netifaces.ifaddresses(interface)
            inet = addrs.get(netifaces.AF_INET, [{}])[0].get('addr')
            if inet:
                return inet
        except Exception:
            pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return ""

def build_header_json(name, camera_type, mac, ip_addr, frame_size):
    obj = {"name": name, "camera_type": camera_type, "mac": mac, "ip_addr": ip_addr, "frame_size": frame_size}
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def write_uint32_be(s, v):
    s.sendall(struct.pack(">I", v))

def connect_server(backoff_base=1.0, backoff_max=10.0):
    backoff = backoff_base
    while running:
        try:
            LOG.info("Connecting to server %s:%d ...", SERVER_IP, SERVER_PORT)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.settimeout(10.0)
            s.connect((SERVER_IP, SERVER_PORT))
            s.settimeout(0.5)
            LOG.info("Connected to server")
            return s
        except Exception as e:
            LOG.warning("Connect failed: %s; retrying in %.1fs", e, backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, backoff_max)
    return None

def capture_jpeg_from_cv(picam2):
    # Grab numpy array directly from the CSI camera via libcamera
    frame = picam2.capture_array()
    if frame is None:
        raise RuntimeError("picamera2 capture failed")
        
    # encode to JPEG via OpenCV
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
    ret, buf = cv2.imencode('.jpg', frame, encode_param)
    if not ret:
        raise RuntimeError("JPEG encode failed")
    return buf.tobytes()

def main_loop():
    global sock, running
    if cv2 is None:
        LOG.error("cv2 not available. Install python3-opencv or opencv-python.")
        return 1
    if Picamera2 is None:
        LOG.error("Picamera2 not available. Install python3-picamera2.")
        return 1

    mac = get_mac_no_colon(NET_INTERFACE)
    LOG.info("MAC: %s", mac)
    ip_addr = get_ip_addr(NET_INTERFACE)
    LOG.info("IP: %s", ip_addr or "<none>")

    try:
        w, h = [int(x) for x in RESOLUTION.split("x")]
    except Exception:
        w, h = 800, 600

    # Initialize and configure Picamera2 for OpenCV BGR format
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"format": "BGR888", "size": (w, h)}
    )
    picam2.configure(config)
    picam2.start()
    
    # allow warmup
    time.sleep(1.0)

    sock = connect_server()
    if sock is None:
        LOG.error("Could not connect to server")
        picam2.stop()
        return 1

    backoff_base = 1.0
    backoff_max = 10.0
    backoff = backoff_base

    try:
        while running:
            # detect server close
            try:
                sock.settimeout(0.01)
                try:
                    data = sock.recv(1024)
                    if data == b'':
                        raise ConnectionResetError("server closed")
                except socket.timeout:
                    pass
                finally:
                    sock.settimeout(0.5)
            except Exception as e:
                LOG.warning("Server connection lost: %s", e)
                try:
                    sock.close()
                except Exception:
                    pass
                sock = None

            if sock is None:
                sock = connect_server(backoff_base=backoff, backoff_max=backoff_max)
                if sock is None:
                    LOG.error("Reconnect failed; exiting")
                    break
                backoff = backoff_base
                ip_addr = get_ip_addr(NET_INTERFACE)

            try:
                jpeg = capture_jpeg_from_cv(picam2)
            except Exception as e:
                LOG.exception("Capture failed: %s", e)
                time.sleep(1.0)
                continue

            header = build_header_json(CAMERA_NAME, CAMERA_TYPE, mac, ip_addr, len(jpeg))
            try:
                write_uint32_be(sock, len(header))
                sock.sendall(header)
                write_uint32_be(sock, len(jpeg))
                sock.sendall(jpeg)
                LOG.debug("Sent header %d and image %d", len(header), len(jpeg))
                backoff = backoff_base
            except Exception as e:
                LOG.warning("Send failed: %s", e)
                try:
                    sock.close()
                except Exception:
                    pass
                sock = None

            time.sleep(max(0.0, CAPTURE_INTERVAL_MS / 1000.0))
    except KeyboardInterrupt:
        LOG.info("Interrupted")
    finally:
        running = False
        try:
            if sock:
                sock.close()
        except Exception:
            pass
        picam2.stop()
    return 0

def handle_sigterm(signum, frame):
    global running
    LOG.info("Signal %s received, shutting down", signum)
    running = False

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)
    LOG.info("Starting OpenCV camera sender")
    sys.exit(main_loop() or 0)
