# Pi Camera Sender (ESP32-compatible)

This service captures JPEG frames from a Raspberry Pi Camera v1 and sends them to a TCP ingest server
using the same framing protocol as an ESP32 camera client.

## Requirements
- Raspberry Pi 3B (or similar) with Pi Camera v1 connected and enabled.
- Raspberry Pi OS (Lite or Desktop) with Python 3.
- Ingest server reachable at `INGEST_SERVER_IP:INGEST_SERVER_PORT`.

## Install steps (example)
1. Update system and install dependencies:
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y python3 python3-pip python3-venv git

2. Enable camera:
   sudo raspi-config
   -> Interface Options -> Camera -> Enable
   Reboot if prompted.

   If using newer Raspberry Pi OS where legacy camera stack is disabled, install/enable legacy camera support or use `libcamera`/`picamera2`. This script uses `picamera` (legacy).

3. Install Python packages:
   Option A: system-wide
     sudo pip3 install picamera netifaces

   Option B: virtualenv (recommended)
     sudo -u pi -H bash -lc "python3 -m venv /home/pi/pi_cam_env && source /home/pi/pi_cam_env/bin/activate && pip install --upgrade pip && pip install picamera netifaces"

4. Place the script:
   sudo mkdir -p /opt/RaspberryCam
   sudo chown pi:pi /opt/RaspberryCam
   cp picamclient.py /opt/RaspberryCam/
   chmod +x /opt/RaspberryCam/picamclient.py

5. Create systemd service:
   Create `/etc/systemd/system/picamclient.service` (see provided unit file).
   Edit environment variables inside the unit or create an EnvironmentFile.

6. Start service:
   sudo systemctl daemon-reload
   sudo systemctl enable picamclient.service
   sudo systemctl start picamclient.service
   sudo journalctl -u picamclient -f

## Configuration
- `INGEST_SERVER_IP` and `INGEST_SERVER_PORT` must point to your ingest server.
- `CAMERA_NAME` and `CAMERA_TYPE` identify the device to the server.
- `CAPTURE_INTERVAL_MS` controls capture interval (ms).
- `NET_INTERFACE` selects which network interface to read IP/MAC from (e.g., `eth0`, `wlan0`).
- `JPEG_QUALITY` and `RESOLUTION` can be set via environment variables.

## Notes and troubleshooting
- If the camera fails to initialize, ensure the camera ribbon is seated and `raspi-config` camera interface is enabled.
- If the server rejects frames, check server logs and ensure the framing protocol matches (4‑byte BE header length, header JSON, 4‑byte BE image length, JPEG bytes).
- To test locally, run the script manually:
  python3 /opt/RaspberryCam/picamclient.py

## Security
- The connection is plain TCP. If you need encryption, run the ingest server behind TLS or use an SSH tunnel / VPN.

