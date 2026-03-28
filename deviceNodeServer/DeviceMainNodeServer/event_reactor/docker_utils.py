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
