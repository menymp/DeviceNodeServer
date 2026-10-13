# Manual Device Deployments

The repository's server runtime is moving to a service-sliced Compose deployment, but hardware-side software is deployed separately. Compose does not flash firmware, install Pi-side services, or manage the lifecycle of those devices. The user reports the Dockerized server as a recent and still somewhat functional migration from the previous codebase; keep that migration context in mind when investigating behavior that spans server and devices.

## Raspberry Pi Camera Sender

| Item | Location / behavior |
| --- | --- |
| Source | `deviceNodeServer/Raspberry/RaspberryCam/picamclient.py` |
| Pi service unit | `deviceNodeServer/Raspberry/RaspberryCam/picamclient.service` |
| Pi deployment notes | `deviceNodeServer/Raspberry/RaspberryCam/README.md` |
| Installation target in the example | `/opt/RaspberryCam/`; systemd unit is installed under `/etc/systemd/system/` and enabled on the Pi. |
| Server receiver | `deviceNodeServer/DeviceMainNodeServer/VideoHandler_v2/main.py` |
| Server port configuration | `DEVICE_SOCKET_PORT` in Compose environment; the current local `.env` sets it to `8072`, and Compose publishes that port. |

The client captures JPEG frames, reconnects to the server with backoff, and sends this TCP frame repeatedly:

1. Four-byte big-endian JSON-header length.
2. UTF-8 JSON header.
3. Four-byte big-endian JPEG length.
4. JPEG payload.

The receiver reads the same framing, validates lengths, stores the newest frame per camera in memory, and makes it available to the HTTP video path. The Pi connects directly to the server host and published TCP port; this ingest traffic is not routed through Caddy. Ensure the address and port configured on the Pi match the server's reachable address and `DEVICE_SOCKET_PORT`.

The example systemd unit currently has an empty `INGEST_SERVER_IP`, so the Pi deployment must provide the correct server address (by editing the unit or supplying an environment file). It sets port `8072`; keep this aligned with server configuration.

### Contract Caveat

The Pi sender builds a header with a `camera_type` field. The current video receiver passes `hdr.get("type")` to `FrameServerConstructor.processCameraHeader`, which stores that value as the camera type. The receiver still uses `name` and `mac` to form its camera ID, but the type value will not come from the Pi's `camera_type` field as currently written. Confirm the intended header contract before relying on camera type metadata or changing either side.

The Pi README also describes the script as using legacy `picamera`, while the current script imports `Picamera2`. Treat the code and installed Pi dependencies as authoritative until that README is reconciled.

## ESP32 And MicroPython Devices

- ESP32 projects are under [`ESP32 Nodes Network/`](../ESP32%20Nodes%20Network/); MicroPython projects are under [`microPythonNodes/`](../microPythonNodes/).
- Their code is built/flashed or otherwise deployed to individual boards outside Compose. Exact steps are project-specific and should be taken from the firmware folder and its board/toolchain configuration.
- OTA-related directories and the separate `phpMpyOta/` service exist, but this map does not assume all firmware families use that updater.
- Runtime integration may use MQTT, TCP camera ingest, or another project-specific protocol. Trace the selected firmware's implementation and server endpoint rather than inferring its transport from its directory name.

## Investigation Checklist

When a hardware device stops working after a server change, verify both deployment sides:

- Is the device running the expected firmware/script version and configuration?
- Can it reach the server host and the specific published port/protocol?
- Does the server-side service listen on that port and parse the same message fields/framing?
- Are required MySQL/MQTT/device identity records current where the protocol depends on them?
- Are systemd/service logs on the device and the corresponding Compose service logs consistent?