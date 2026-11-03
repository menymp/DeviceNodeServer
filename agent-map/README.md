# Agent Map

A maintained navigation layer for understanding this repository without rereading the entire tree. This is a derived map, not a replacement for implementation or deployment configuration.

## Start Here

- [Runtime architecture](runtime-architecture.md): Compose services, responsibilities, routes, dependencies, and active versus commented services.
- [Codebase tour](codebase-tour.md): Top-level directory ownership, shared infrastructure, and useful entry points.
- [Firmware and tests](firmware-and-tests.md): Embedded firmware families and the currently identified test/example code.
- [Manual device deployments](manual-device-deployments.md): Raspberry Pi camera systemd deployment, embedded firmware deployment boundary, and the Pi-to-video-server protocol.
- [Development roadmap](development-roadmap.md): Proposed firmware deployment/testing and management UI/UX work, with open scope and acceptance questions.

## Sources Of Truth

- Runtime deployment: [`docker-compose.yml`](../docker-compose.yml), with request routing in [`Caddyfile`](../Caddyfile).
- Module behavior: implementation and local README files under each module.
- Hardware/firmware behavior: the individual firmware project and its device protocol.
- Database shape/bootstrap: files under [`sql/`](../sql/).
- This map summarizes those sources and may lag them; confirm behavior in source before making changes.

## Map Conventions

- **Compose-active** means a service is declared in the current Compose file; it does not prove the container is presently running or healthy.
- **Commented/legacy** means Compose contains an explicitly commented alternative or the directory is not referenced by the active service definition.
- Unknown or inferred responsibilities are labeled as such rather than treated as established behavior.
- Never put secret values, private keys, or credential contents in this directory.

## Updating The Map

When architecture changes, update the matching page and keep this index current. For a new runtime service, record its Compose key, Dockerfile, startup entry point, dependencies, ports/routes, and persistent mounts. For firmware, tests, or development workflows, update the corresponding specialized page.
