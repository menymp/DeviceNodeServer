# Runtime Architecture

Operational map derived from [`docker-compose.yml`](../docker-compose.yml). Service declarations are not evidence that a service is currently running. The central request-routing layer is [`Caddyfile`](../Caddyfile).

## Deployment Layers

This is a hybrid deployment, not a Compose-only system. The server-side core has recently been split into Compose services; device-side software remains separately deployed to its hardware. Raspberry Pi camera clients run as host systemd services, while ESP32 and MicroPython projects are deployed/flashed to their target boards. These hardware deployments communicate with the server over configured network interfaces and are not managed by the Compose lifecycle. See [manual device deployments](manual-device-deployments.md).

For the Pi camera path, the sender's default TCP port `8072` matches the current `DEVICE_SOCKET_PORT` value and the Compose-published device socket. The listener is in `VideoHandler_v2/main.py`; Caddy does not proxy this raw TCP ingest connection.

## Request Paths

| Client path / interface | Compose destination | Notes |
| --- | --- | --- |
| `/backend/*` | `php-node-service:80` | PHP REST API; Caddy strips the `/backend` prefix with `handle_path`. |
| `/socket/*` | `websocket-service:${WEBSOCKET_PORT}` | WebSocket command interface; Caddy strips `/socket`. |
| `/video/*` | `video-composer-service:${VIDEO_SEED_PORT}` | Video feed; Caddy strips `/video`. |
| Other HTTP(S) paths | `react-device-manager-ui:${REACT_MANAGER_PORT}` | React device manager UI. |
| `/health` | Caddy | Returns `ok`; handled before the static UI route. |
| `${PHP_OTA_PORT}` host port | `php-ota-service:80` | OTA PHP service is directly port-published in Compose, outside the Caddy routes above. |
| MQTT ports | `mqtt-broker` | Mosquitto broker is exposed using configured broker port plus port 9001. |
| XBee serial device | `xbee-bridge-service` | Host serial device mapped into a privileged container. |

## Compose Services

| Service | Implementation / build source | Responsibility and dependencies |
| --- | --- | --- |
| `device-manager-service` | `deviceNodeServer/DeviceMainNodeServer/DeviceManager/`; Dockerfile builds `main.py` | Device command/measure management; MySQL and Mosquitto. The local README describes device objects and MQTT communication. |
| `node-device-manager-service` | `deviceNodeServer/DeviceMainNodeServer/NodeDeviceManager/`; Dockerfile builds `main.py` | Discovers nodes' child devices/manifests and updates database records; MySQL and Mosquitto. |
| `video-composer-service` | `deviceNodeServer/DeviceMainNodeServer/VideoHandler_v2/`; Dockerfile builds `main.py` | Video/frame handling; MySQL, Mosquitto dependency, and published video/device socket ports. |
| `websocket-service` | `deviceNodeServer/DeviceMainNodeServer/WSocketServerManager/`; Dockerfile builds `main.py` | WebSocket UI command transport; depends on device manager and PHP API. README describes a ZMQ connection to DeviceManager. |
| `php-node-service` | `phpWebApp/` | Slim/PDO/JWT API for the UI; MySQL, Mosquitto dependency, database secret and JWT key secrets. Caddy routes `/backend/*` here. |
| `react-device-manager-ui` | `nodePackages/device-mgr-ui/` | React UI; configured with API, command-WebSocket, and video URLs. Caddy routes the remaining web requests here. |
| `caddy` | `caddy:2` | Public HTTP/HTTPS entry point on host ports 80 and 443; proxies UI, API, WebSocket, and video routes. |
| `reactor-service` | `deviceNodeServer/DeviceMainNodeServer/event_reactor/` | Polls database script instances and can create/run handler containers through the Docker socket. Uses the registry/image builder workflow and shared Python modules mounted from the repository. |
| `registry` | `registry:2` | Local container image registry, exposed on host port 5000 with persistent `registry_data`. |
| `generic-builder` | Kaniko executor with `docker_base_image/` mounted as workspace | Builds/publishes `local/docker_base_image:dev` into the local registry; reactor waits for this image. |
| `php-ota-service` | `phpMpyOta/` | PHP-based firmware/OTA endpoint; uses shared config mount and directly publishes `${PHP_OTA_PORT}`. Its README describes a versioned update/rollback workflow but is explicitly early-stage. |
| `nodes-db` | `mysql:8.0` | Primary MySQL service; initializes from `sql/nodeServerModel.sql` and `sql/nodeServerSeeds.sql`, persists `db_data`, and has a health check. |
| `mqtt-broker` | `eclipse-mosquitto:2.0` | Device messaging broker; config/data/log mounts under `mosquitto/`. |
| `maintenance-service` | `deviceNodeServer/DeviceMainNodeServer/MaintenanceService/` | Database-backed maintenance process; waits for healthy MySQL. See its local README for details. |
| `xbee-bridge-service` | `deviceNodeServer/xbeeNetwork/xbeeCoordinator/` | XBee network bridge; needs serial access, MySQL, Mosquitto, and NodeDeviceManager. The Compose declaration requests privileged mode. |
| `telegram-executor-service` | `deviceNodeServer/DeviceMainNodeServer/TelegramCommandExecutor/` | Telegram command executor; integrates with device manager and video service. |
| `scheduler-service` | `deviceNodeServer/DeviceMainNodeServer/SchedulerService/` | Database-backed scheduler with MQTT configuration and a 30-second DB poll setting. |

## Persistent State And Secrets

- Named volumes: `db_data`, `registry_data`, `caddy_data`, `caddy_config`.
- Bind-mounted broker state/config: `mosquitto/data`, `mosquitto/log`, `mosquitto/config/mosquitto.conf`.
- Compose reads host `.env` substitutions and mounts password/JWT secrets from `secrets/`. The map intentionally records locations only, never values.
- Several Python services still bind-mount `DeviceMainNodeServer/config.ini`; Compose comments call this an outdated configuration mechanism.
- The reactor mounts the Docker socket, giving it container-management capability. Treat changes to its image/build/runtime behavior as deployment-sensitive.

## Explicitly Inactive Or Commented Compose Entries

- `handler_test_env` is commented out and marked for process testing.
- The older `VideoHandler/` service definition is commented out and labeled outdated; active video service is `VideoHandler_v2/`.
- `VideoHandler_v2/legacyVideoServermain.py` is present, but its runtime status is not established by Compose alone.
