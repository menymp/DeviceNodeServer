'''
event_reactor/docker_utils.py
'''

import logging
from docker import DockerClient
from docker.errors import NotFound, APIError
from docker.types import Mount

logger = logging.getLogger("docker_utils")

# If more shared modules added in the future, include the directory here 
mounts = [
    Mount(target="/app/ConfigsUtils",
          source="/app/ConfigsUtils",
          type="bind",
          read_only=True),
    Mount(target="/app/DButils",
          source="/app/DButils",
          type="bind",
          read_only=True),
    Mount(target="/app/DockerUtils",
          source="/app/DockerUtils",
          type="bind",
          read_only=True),
]

class DockerRunner:
    def __init__(self, base_url=None):
        # base_url e.g. 'unix://var/run/docker.sock' or None to use env
        logger.info("base URL:" + str(base_url))
        self.client = DockerClient(base_url=base_url) if base_url else DockerClient.from_env()

    def build_image(self, context_path, dockerfile="Dockerfile", tag=None, rm=True, pull=False):
        """
        Build an image from a local context directory accessible to the reactor process.
        context_path: absolute path inside reactor container (e.g., /host_repo/event_reactor/handlers/rfid)
        tag: image tag to apply (e.g., local/rfid-worker:dev)
        """
        try:
            logger.info("building image from %s dockerfile=%s tag=%s", context_path, dockerfile, tag)
            image, logs = self.client.images.build(path=context_path, dockerfile=dockerfile, tag=tag, rm=rm, pull=pull)
            # optional: stream logs for debugging
            for chunk in logs:
                if isinstance(chunk, dict) and 'stream' in chunk:
                    logger.debug(chunk['stream'].strip())
            return True
        except Exception as e:
            logger.exception("unexpected error building image from %s", context_path)
            logger.exception(e)
            return False

    def ensure_image(self, image, build_info=None):
        """
        Ensure image exists locally. If not found, try pull; if pull fails and build_info provided, attempt build.
        build_info: dict {build_context, dockerfile, image_tag}
        """
        try:
            self.client.images.get(image)
            return True
        except NotFound:
            logger.info("image %s not found locally; attempting pull", image)
            try:
                self.client.images.pull(image)
                return True
            except APIError:
                logger.exception("failed to pull image %s", image)
                if build_info:
                    ctx = build_info.get("build_context")
                    df = build_info.get("dockerfile") or "Dockerfile"
                    tag = build_info.get("image_tag") or image
                    logger.info("build info: '" + str(ctx) + "' '"+ str(df) + "' '" + str(tag) + "'")
                    # context_path must be accessible to reactor (mounted)
                    return self.build_image(ctx, dockerfile=df, tag=tag)
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
                network=network,
                mounts=mounts
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
