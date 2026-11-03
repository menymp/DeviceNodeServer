# Codebase Tour

Repository map for locating implementation areas. The root directory mixes deployment files, active services, firmware projects, and older experiments.

## Top-Level Areas

| Path | Role |
| --- | --- |
| `docker-compose.yml`, `Caddyfile`, `.env` | Homelab service orchestration, routing, and local deployment variables. Do not copy `.env` values into notes. |
| `deviceNodeServer/DeviceMainNodeServer/` | Main Python server collection, including Compose services, shared utilities, legacy servers, and test/example environments. |
| `deviceNodeServer/xbeeNetwork/` | XBee network code, including the Compose coordinator service and Arduino-side sample firmware under `xbeeFirmwares/`; see [firmware and tests](firmware-and-tests.md). |
| `deviceNodeServer/dvrClient/` | DVR scanning and a test script (`dvrClientTest.py`). |
| `deviceNodeServer/Libraries/` | Shared Python/device libraries mounted into some services. |
| `deviceNodeServer/GSM_BaseAlarm/` | Hardware-oriented project; current deployment ownership is not established by Compose. |
| `deviceNodeServer/Raspberry/` | Raspberry Pi-side applications. `RaspberryCam/` contains a manually installed camera sender and systemd unit; see [manual device deployments](manual-device-deployments.md). |
| `ESP32 Nodes Network/` | ESP32 firmware projects, including camera, garden, node, RFID, PIR, output, OTA, and bridge examples. |
| `microPythonNodes/` | MicroPython and Raspberry Pi Pico W projects, shared libraries, OTA, sensor and appliance examples. |
| `reactor/handlers/` | Handler definitions/configuration mounted into the reactor; inspect handler folders and Dockerfiles for execution details. |
| `nodePackages/device-mgr-ui/` | Main system management frontend (React); start at `src/App.tsx`. It uses the PHP REST-like API plus WebSocket command and video services. Compose service: `react-device-manager-ui`; see [runtime architecture](runtime-architecture.md) for routes. |
| `phpWebApp/` | REST-like PHP backend API for the management UI, not the frontend. `src/` contains Slim routes/controllers, middleware, repositories, services, and dependencies; Caddy exposes it under `/backend/`. |
| `phpMpyOta/` | Intended future PHP server for MicroPython OTA updates. The version/rollback workflow is still a test/early implementation with TODOs; a Compose declaration does not mean the OTA system is complete. |
| `sql/` | MySQL initialization/model scripts and seed data, plus model artifacts. |
| `mosquitto/` | Broker configuration and host-mounted runtime data/log directories. |
| `docker_base_image/` | Base image built by the Compose Kaniko helper for reactor handler workloads. |
| `systemd/` | Host-level systemd integration notes/service definition. |
| `config/`, `phpconfig/`, `phpconfigs/`, `certs/`, `secrets/` | Deployment configuration, certificates, and secret material. Do not publish credential contents. |
| `InstallationNotes.txt`, `docker-deploy-notes.txt`, `pending.txt`, `controlsTemplates.txt` | Operational/project notes and templates; verify freshness before relying on procedures. |

## Main Python Server Collection

Within `DeviceMainNodeServer/`, Compose-active module ownership is detailed in [runtime architecture](runtime-architecture.md). Additional areas worth locating:

- `ConfigsUtils/`, `DButils/`, `DockerUtils/`: shared configuration, database, and Docker helpers mounted into runtime containers.
- `event_reactor/`: reactor application and runtime helpers. Compose maps this to `reactor-service`.
- `handler_test_env/`: test-environment implementation; its Compose service is commented out.
- `DeviceTestEmulator/`: device emulation/test support; runtime integration needs local inspection.
- `VideoHandler/`: older video implementation; current Compose target is `VideoHandler_v2/`.
- `deviceNodeServer.py`, `pythonServer.py`, `serverStart.py`, `Cliente.py`, `cameraServiceController.py`: root-level server/client/camera code outside current Compose service definitions; treat as separate/legacy or development paths until a caller is found.

## Migration Boundary

The server's core has recently moved from the previous codebase toward a service-sliced Docker Compose deployment. The user describes the current stack as somewhat functional, so treat Compose as the current server deployment definition but do not assume migration is complete. Device firmware and hardware-side clients are still separately deployed; this includes Raspberry Pi camera sender services and ESP32/MicroPython firmware. Older code in this repository may therefore remain in use on devices even when it is no longer part of the server containers.

## Cross-Cutting Architecture

- MySQL is the shared relational store. Compose initializes the principal model/seeds from `sql/`.
- Mosquitto is the device messaging backbone.
- Device discovery is documented under `NodeDeviceManager`; command/measure handling is documented under `DeviceManager`.
- The UI talks to a PHP HTTP API, a WebSocket command path, and a video endpoint through Caddy. Verify payloads/contracts in both frontend and backend source before changing interfaces.
- The reactor is distinct from the fixed Compose services: it reads database instances and creates handler containers dynamically.

## Reading Order For A Change

1. Identify whether the target is a deployed service, firmware project, or supporting/legacy code.
2. For deployed Python services, start at the module Dockerfile and `main.py`, then follow imported shared utilities.
3. For user-visible web behavior, follow the UI component/service to the corresponding Caddy route and PHP/WebSocket/video implementation.
4. For device behavior, trace the firmware protocol through MQTT/node discovery and device command handling.
5. Check focused tests and deployment mounts/environment before changing runtime assumptions.
