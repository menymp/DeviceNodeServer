# Firmware And Tests

This page indexes the embedded-code families and currently identifiable tests/examples. Directory names are inventory, not proof of supported hardware or production status.

## Firmware Families

### ESP32

Root: [`ESP32 Nodes Network/`](../ESP32%20Nodes%20Network/)

- `BasicOTABaseFirmware/`, `ESP32_OTABlink/`: OTA/base and blink examples.
- `ESP32_GARDENFirmware1/`: garden-oriented firmware.
- `ESP32_NodeFirmware1/`, `NodeBridgeUino/`: node and bridge firmware.
- `ESP32_OPEN_PLC_CARRIER_TEST/`: carrier/PLC experiment.
- `ESP32_OutputsNodeFirmware1/`: output control node.
- `ESP32_PIRFirmware1/`: PIR sensor node.
- `ESP32_RFIDFirmware1/`, `ESP32_RFID_Async/`: RFID implementations.
- `CAMERA_TAKE_PHOTO/`, `ESP32_VIDEO_CLIENT_V2/`: camera/video clients.

The family README says the intention is to build shared base libraries and generic configurations. Device protocol details should be verified in the relevant sketch/library rather than inferred from the folder name.

### MicroPython

Root: [`microPythonNodes/`](../microPythonNodes/)

- `COMMON_LIBRARIES/`: shared modules.
- `ESP32_GAS_SPECTROMETER/`, `ESP32_NODE_BRIDGE_USE_EXAMPLE/`, `ESP32_OTA_APACHE/`, `ESP32_REFLOW_OVEN/`: ESP32 examples/projects.
- `RPI_PICOW_GARDEN/`: Raspberry Pi Pico W project.
- `MOCK_TEST_EXAMPLE/`: mock/test example.

The root README lists sensor/library references but does not define a repository-wide firmware test workflow.

### XBee Arduino Samples

Root: [`deviceNodeServer/xbeeNetwork/xbeeFirmwares/`](../deviceNodeServer/xbeeNetwork/xbeeFirmwares/)

- [`arduinoDeviceTest/`](../deviceNodeServer/xbeeNetwork/xbeeFirmwares/arduinoDeviceTest/) contains `arduinoDeviceTest.ino`, a simple Arduino sketch that emulates an XBee network device. It receives XBee packets, toggles an output for `a`/`b`, and replies with analog sensor and output state.
- `simpleTxDebug/` and `xbeeClient_v2/` are additional XBee sketches; inspect their sources for board/library and behavior details.
- This is device-side example firmware, separate from the server coordinator at `deviceNodeServer/xbeeNetwork/xbeeCoordinator/`, which is a Compose service.

## Deployment Boundary

These firmware projects are deployed to their hardware separately from the server's Compose stack. Deployment may mean building/flashing firmware or using a project-specific OTA process; do not assume every project uses the PHP OTA service. See [manual device deployments](manual-device-deployments.md) for the server/device boundary and the concrete Raspberry Pi sender example.

## Test And Example Inventory

### Explicit Python Test-Like Files

- `deviceNodeServer/dvrClient/dvrClientTest.py`: DVR client test script.
- `deviceNodeServer/DeviceMainNodeServer/webcamTest.py`: webcam test script.
- `deviceNodeServer/xbeeNetwork/xbeeCoordinator/testScripts/pcDeviceTest.py`: XBee/PC device script.
- `deviceNodeServer/DeviceMainNodeServer/event_reactor/handlers/rfid/worker_test.py`: RFID worker test.
- `deviceNodeServer/DeviceMainNodeServer/event_reactor/handlers/camera/test.py`: camera handler test.

Names alone do not establish whether these are automated, hardware-dependent, or safe to run without devices/services. Inspect each script before execution.

### Other Test Infrastructure

- `nodePackages/device-mgr-ui/src/App.test.tsx` and `setupTests.ts`: frontend test scaffolding; UI README documents `yarn test`.
- `deviceNodeServer/DeviceMainNodeServer/handler_test_env/`: dedicated process test environment, but its Compose service is commented out.
- `deviceNodeServer/DeviceMainNodeServer/DeviceTestEmulator/`: device emulator area; inspect for available harnesses.
- Firmware folders include hardware examples; no unified test runner was identified from the current root-level inventory.

## Validation Guidance

Before running a test, check its imports, expected working directory, required broker/database, and hardware/serial dependencies. Prefer focused module instructions and test configuration over guessing a repository-wide command. Update this page when a repeatable test command or test ownership is confirmed.
