# Development Roadmap

This is a proposed planning page based on the user's stated goals, not a delivery schedule or a claim that the work is underway. The order below follows the user's requested sequence: deploy/test Node Bridge clients, complete the UI/UX work in listed order, then develop the XBee weather-station monitor. Firmware deployment is performed on hardware outside the server's Compose lifecycle; see [firmware and tests](firmware-and-tests.md) and [manual device deployments](manual-device-deployments.md).

## 1. Deploy And Test Node Bridge Clients

Deploy and validate the modernized clients in [`ESP32 Nodes Network/`](../ESP32%20Nodes%20Network/) and [`microPythonNodes/`](../microPythonNodes/) that use the Node Bridge client protocol. The scoped boards/languages are:

- ESP32 using C++ with Arduino.
- ESP32 using MicroPython.
- Raspberry Pi Pico W using MicroPython only.

Suggested outcomes:

- Identify the exact client projects and firmware revisions within the stated board/language scope, plus their build/flash process.
- Build and deploy to representative hardware, then exercise the Node Bridge protocol against the intended server setup.
- Record protocol compatibility, observed behavior, logs, known limitations, and repeatable test steps.
- Record the tested hardware and whether the client implementations are ready for broader deployment.

Questions:

- Which exact project folders and client revisions are the modernized Node Bridge clients in each repository?
- What is the target Node Bridge/server environment, and what end-to-end behavior counts as a pass (discovery, telemetry, commands, reconnects, or all of these)?

## 2. Modernize The Management UI In Requested Order

The main frontend is [`nodePackages/device-mgr-ui/`](../nodePackages/device-mgr-ui/); its backend is [`phpWebApp/`](../phpWebApp/). Complete the following UI capabilities in the order shown. The existing scheduler and reactor are potential integration points, not assumptions about final feature design. See [runtime architecture](runtime-architecture.md).

### Event Schedule Manager

Add UI workflows for viewing and managing scheduled events, using the existing scheduler service where its current behavior and data model fit.

Questions:

- Which event types should be schedulable, and what create/edit/pause/run-now/history actions are required?
- What recurrence, timezone, and missed-run behavior should users see and control?

### Custom Script Manager

Build a manager for event reactor classes (handlers). Classes are in [`event_reactor/handlers/`](../deviceNodeServer/DeviceMainNodeServer/event_reactor/handlers/); the current handler directories are `camera/` and `rfid/` (two areas). Users should be able to add a script instance, enable or disable it, and provide the configuration relevant to its class. When new handler classes are released in code, they should become available in the UI menu without hard-coding the current class list into the frontend.

Plan for class discovery and configuration schemas to come from an appropriate backend/source-of-truth contract; verify the existing reactor and database model before choosing how this works.

Questions:

- Does “add a script” mean creating a configured instance of a released handler class, rather than authoring or uploading executable code in the UI?
- How should the UI discover new classes after code deployment: on page load/API query, an explicit catalog refresh, or another release step?
- What configuration schema should each class expose, and which user roles may add, enable, disable, or edit instances?

### Controls Dashboard Modernization

Modernize the controls dashboard for clear device state and efficient command interaction while preserving existing device/API behavior unless intentionally changed.

Questions:

- Which current dashboard views or controls are in scope, and what are the main usability problems to solve?
- Which device states, measurements, and actions should be prominent, and are there roles or user-specific layouts?

### Mobile-First App Changes

Make the management workflows usable on small screens, prioritizing the workflows identified above. Treat installable/PWA behavior as undecided until confirmed.

Questions:

- Is the target a responsive web app, an installable PWA, or a separately packaged mobile app?
- Which mobile browsers/devices and workflows are the acceptance baseline? Is offline use or push notification support required?

### Image Processing Workflows

Design the UI and backend flow for image processing as a distinct capability; determine how it relates to the existing video/image services before selecting an implementation.

Questions:

- What are the image sources, required processing steps, and expected outputs or downstream consumers?
- Does this cover still images, live video frames, or both? Is processing automatic, user-triggered, or a reviewable pipeline?
- Are there constraints for processing latency, storage/retention, hardware acceleration, or supported formats/models?

## 3. XBee Weather-Station Monitoring

Develop an Arduino C++ weather-station monitor using the existing clients and tools under [`deviceNodeServer/xbeeNetwork/`](../deviceNodeServer/xbeeNetwork/), including the XBee coordinator and firmware resources where appropriate. This project follows the original client-deployment and UI/UX sequence above; it is a separate XBee track, not a Node Bridge client.

Suggested outcomes:

- Identify the XBee client/tooling and coordinator paths that fit this station, and define the weather-station hardware and telemetry contract.
- Implement and deploy the Arduino C++ station client using the established XBee-side tools/protocol.
- Validate end-to-end sensor telemetry through the coordinator to its intended server/database or UI consumer.
- Document the build, flash, configuration, and field-test procedure.

Questions:

- Which XBee radio/module, Arduino board, and weather sensors are intended?
- Which measurements, units, sampling interval, and delivery/retry behavior are required?
- Where should received measurements be stored and displayed, and does this depend on the earlier UI work?

## Cross-Cutting Planning Questions

- What release environment and regression checks should be used for UI/API changes?

## Planning Notes

- Keep this page at the goal and decision level. Move confirmed protocols, API contracts, test commands, and deployment procedures into their implementation-focused map pages.
- Reuse existing backend services where appropriate, but verify their current contracts and limitations before treating them as feature-complete foundations.
- Update this roadmap when scope, ordering, or acceptance criteria are confirmed; do not treat open questions as settled requirements.