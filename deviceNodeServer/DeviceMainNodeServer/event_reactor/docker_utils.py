'''
event_reactor/docker_utils.py
'''

import logging
from docker import DockerClient
from docker.errors import NotFound, APIError

logger = logging.getLogger("docker_utils")

class DockerRunner:
    def __init__(self, base_url=None):
        # base_url e.g. 'unix://var/run/docker.sock' or None to use env
        self.client = DockerClient(base_url=base_url) if base_url else DockerClient.from_env()

    def ensure_image(self, image):
        try:
            self.client.images.get(image)
            return True
        except NotFound:
            logger.info("pulling image %s", image)
            try:
                self.client.images.pull(image)
                return True
            except APIError:
                logger.exception("failed to pull image %s", image)
                return False
        except Exception:
            logger.exception("error checking image %s", image)
            return False

    def run_container(self, name, image, env=None, mounts=None, labels=None, restart_policy=None, detach=True, network=None):
        """
        Create and start a container. If a container with same name exists, try to remove it first.
        - env: dict
        - mounts: list of docker.types.Mount or simple dicts (handled minimally)
        - restart_policy: dict like {"Name":"on-failure","MaximumRetryCount":3}
        """
        try:
            # remove existing container if present
            try:
                existing = self.client.containers.get(name)
                logger.info("removing existing container %s", name)
                existing.remove(force=True)
            except NotFound:
                pass

            env_list = [f"{k}={v}" for k, v in (env or {}).items()]
            host_config = {}
            rp = restart_policy or {}
            # docker-py accepts restart_policy as dict
            container = self.client.containers.run(
                image,
                name=name,
                environment=env_list,
                detach=detach,
                labels=labels or {},
                restart_policy=rp,
                network=network
            )
            return container
        except APIError:
            logger.exception("docker API error running container %s", name)
            return None
        except Exception:
            logger.exception("unexpected error running container %s", name)
            return None

    def get_self_network_name(self, self_container_name=None):
        """
        Return a user network name that the reactor container is attached to.
        If self_container_name is provided, inspect that container; otherwise
        try to find a container with the same hostname or labels (best-effort).
        """
        try:
            # If caller provided the container name, use it
            if self_container_name:
                me = self.client.containers.get(self_container_name)
            else:
                # fallback: try to find a container with the same PID/hostname
                # Best-effort: find containers with label 'com.docker.compose.service=reactor-service'
                containers = self.client.containers.list(all=True, filters={"label": "com.docker.compose.service=reactor-service"})
                me = containers[0] if containers else None

            if not me:
                return None

            nets = me.attrs.get("NetworkSettings", {}).get("Networks", {})
            # prefer non-bridge networks (user networks)
            for net_name in nets.keys():
                if not net_name.startswith("bridge"):
                    return net_name
            # fallback to any network
            return next(iter(nets.keys()), None)
        except Exception:
            logger.exception("failed to detect self network")
            return None

    def stop_and_remove(self, name, timeout=5):
        try:
            c = self.client.containers.get(name)
            c.stop(timeout=timeout)
            c.remove()
        except NotFound:
            return
        except Exception:
            logger.exception("failed to stop/remove %s", name)

    def inspect(self, name):
        try:
            c = self.client.containers.get(name)
            return c.attrs
        except NotFound:
            return None
        except Exception:
            logger.exception("inspect failed for %s", name)
            return None

    def wait(self, container, timeout=None):
        try:
            return container.wait(timeout=timeout)
        except Exception:
            logger.exception("wait failed")
            return None
