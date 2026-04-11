# reactor/start_reactor.py
import os
import sys
import time
import json
import logging
import signal
from threading import Event, Thread

from db_client import DBClient
from docker_utils import DockerRunner

LOG_LEVEL = os.environ.get("REACTOR_LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("start_reactor")

# DB envs
DB_HOST = os.environ.get("DB_HOST", "nodes-db")
DB_NAME = os.environ.get("DB_NAME", "")
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD_FILE = os.environ.get("DB_PASSWORD_FILE", "/run/secrets/db_user_password")

# Optional services integration
WEBSOCKET_PORT = os.environ.get("WEBSOCKET_PORT", "")
DEVICE_MANAGER_LOCAL_CONN = os.environ.get("DEVICE_MANAGER_LOCAL_CONN", "")
VIDEO_HANDLER_LOCAL_CONN = os.environ.get("VIDEO_HANDLER_LOCAL_CONN", "")

# Docker socket (optional override)
DOCKER_BASE_URL = os.environ.get("DOCKER_BASE_URL", None)  # e.g., unix://var/run/docker.sock

POLL_SECONDS = int(os.environ.get("REACTOR_POLL_SECONDS", "5"))
CONTAINER_NAME_PREFIX = os.environ.get("REACTOR_CONTAINER_PREFIX", "handler")

def read_secret(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return None

class Reactor:
    def __init__(self):
        self.stop_event = Event()
        self.db = DBClient()
        self.docker = DockerRunner(base_url=DOCKER_BASE_URL)
        self.running_containers = {}  # instance_id -> container object
        self.poll_thread = None
        self.repo_root = os.environ.get("REACTOR_REPO_ROOT", "/host_repo")

    def init(self):
        pw = read_secret(DB_PASSWORD_FILE)
        self.db.init_connector(user=DB_USER, password=pw, host=DB_HOST, database=DB_NAME)

    def start(self):
        logger.info("starting reactor")
        self.init()
        self.poll_thread = Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()

    def stop(self):
        logger.info("stopping reactor")
        self.stop_event.set()
        # stop containers we started
        for iid, c in list(self.running_containers.items()):
            name = self._container_name(iid)
            try:
                logger.info("stopping container %s for instance %s", name, iid)
                self.docker.stop_and_remove(name)
            except Exception:
                logger.exception("failed to stop container %s", name)
        self.db.close()

    def _container_name(self, instance_id):
        return f"{CONTAINER_NAME_PREFIX}_{instance_id}"

    def _poll_loop(self):
        while not self.stop_event.is_set():
            try:
                logger.info("polling for script instances")
                rows = self.db.get_instances_to_start()
                if not rows:
                    time.sleep(POLL_SECONDS)
                    continue
                logger.info(rows)
                for row in rows:
                    # row may be tuple or dict; support both
                    instance_id = row.get("id") if isinstance(row, dict) else row[0]
                    script_id = row.get("script_id") if isinstance(row, dict) else (row[1] if len(row) > 1 else None)
                    runtime = row.get("runtime") if isinstance(row, dict) else (row[4] if len(row) > 4 else None)
                    cfg_raw = row.get("config_json") if isinstance(row, dict) else (row[6] if len(row) > 6 else None)
                    logger.info("checking instance id" + str(instance_id))
                    cfg = {}
                    if cfg_raw:
                        try:
                            cfg = json.loads(cfg_raw) if isinstance(cfg_raw, str) else cfg_raw
                            logger.info("cnfg " + str(cfg))
                        except Exception:
                            logger.exception("invalid config_json for %s", instance_id)
                    # only handle container runtime in this simplified model
                    # if runtime != "container":
                    #     logger.info("instance %s runtime %s ignored (reactor runs containers only)", instance_id, runtime)
                    #     continue
                    if instance_id in self.running_containers:
                        logger.info("already running id")
                        # optionally check container health
                        continue
                    logger.info("script entry ")
                    # determine image from scripts.entry_point via dbEvents interface
                    # convention: scripts.entry_point for container runtime is the image name
                    # use db_client to fetch script entry (db_client uses dbEvents)
                    # fetch script row to determine canonical image
                    script_row = None
                    try:
                        # db_client._db is the underlying dbScriptActions instance
                        # use the appropriate method your dbScriptActions exposes; common names:
                        # get_script_by_id, get_script, or get_script_by_name
                        logger.info("id script: "  + str(script_id))
                        script_row = self.db._db.get_script_by_id(script_id)[0]
                        logger.info("script entry" + str(script_row))
                    except Exception:
                        logger.info("could not fetch script row for script_id %s; will fallback to config_json", script_id)

                    # normalize script_row to dict
                    script = {}
                    if script_row:
                        if isinstance(script_row, dict):
                            logger.info("dict instance")
                            script = script_row
                        elif isinstance(script_row, (list, tuple)):
                            # adjust indices to your schema; example mapping:
                            logger.info("list tupple")
                            try:
                                script = {
                                    "id": script_row[0],
                                    "name": script_row[1],
                                    "entry_point": script_row[2],
                                    "runtime": script_row[3],
                                    "description": script_row[4],
                                    "build_context": script_row[9],
                                    "dockerfile": script_row[10],
                                    "image_tag": str(script_row[11])
                                }
                                logger.info("script parameters " + str(script))
                            except Exception:
                                logger.error("script info could not be loaded")
                                script = {}
                    
                    # canonical image: prefer image_tag, then entry_point
                    logger.info("entry point " + str(script.get("entry_point")))
                    image = script.get("entry_point")
                    if not image:
                        logger.error("no image specified for script_id %s; skipping instance %s", script_id, instance_id)
                        continue            

                    # prepare build_info if build_context present
                    build_info = None
                    if script.get("build_context"):
                        # build_context is relative to repo root; make absolute path inside reactor container
                        ctx_rel = script.get("build_context")
                        context_path = os.path.join(self.repo_root, ctx_rel)
                        build_info = {
                            "build_context": context_path,
                            "dockerfile": script.get("dockerfile") or "Dockerfile",
                            "image_tag": script.get("image_tag") or image
                        }

                    # ensure image exists (pull or build)
                    ok = self.docker.ensure_image(image, build_info=build_info)
                    if not ok:
                        logger.error("image %s not available for instance %s", image, instance_id)
                        continue
                    # prepare env for container
                    env = {}
                    # pass DB and MQTT envs to worker
                    env.update({
                        "INSTANCE_ID": str(instance_id),
                        "DB_HOST": DB_HOST,
                        "DB_NAME": DB_NAME,
                        "DB_USER": DB_USER,
                        "DB_PASSWORD_FILE": DB_PASSWORD_FILE,
                        "MQTT_BROKER_HOST": os.environ.get("MQTT_BROKER_HOST", "mqtt-broker"),
                        "MQTT_BROKER_PORT": os.environ.get("MQTT_BROKER_PORT", "1883"),
                        "WEBSOCKET_PORT": WEBSOCKET_PORT,
                        "DEVICE_MANAGER_LOCAL_CONN": DEVICE_MANAGER_LOCAL_CONN,
                        "VIDEO_HANDLER_LOCAL_CONN": VIDEO_HANDLER_LOCAL_CONN
                    })
                    logger.info("sub container event" + str(env))
                    # merge instance config into env with prefix HANDLER_CFG_
                    for k, v in (cfg or {}).items():
                        try:
                            env_key = f"HANDLER_CFG_{k.upper()}"
                            env[env_key] = json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                        except Exception:
                            env[env_key] = str(v)
                    # restart policy mapping
                    rp = {}
                    rp_cfg = cfg.get("restart_policy") or {}
                    if rp_cfg:
                        # map to docker restart policy when possible
                        if rp_cfg.get("max_restarts") is not None:
                            rp = {"Name": "on-failure", "MaximumRetryCount": int(rp_cfg.get("max_restarts", 3))}
                        else:
                            rp = {"Name": "no"}
                    # run container
                    name = self._container_name(instance_id)
                    logger.info("container name" + str(name))
                    # compute network name (prefer env, fallback to auto-detect)
                    network_name = os.environ.get("REACTOR_NETWORK")
                    if not network_name:
                        try:
                            # attempt to auto-detect network from reactor container
                            network_name = self.docker.get_self_network_name(os.environ.get("REACTOR_CONTAINER_NAME"))
                        except Exception:
                            network_name = None
                    
                    logger.info("running container")

                    # run container and attach to network
                    container = self.docker.run_container(
                        name=name,
                        image=image,
                        env=env,
                        restart_policy=rp,
                        network=network_name
                    )
                    if container:
                        logger.info("started container %s for instance %s", name, instance_id)
                        self.running_containers[instance_id] = container
                        # record start in DB
                        try:
                            self.db.record_start(instance_id)
                        except Exception:
                            logger.exception("failed to record start for %s", instance_id)
                # check running containers for exit
                for iid, container in list(self.running_containers.items()):
                    info = self.docker.inspect(self._container_name(iid))
                    if not info:
                        # container disappeared
                        logger.warning("container for instance %s not found; marking exit", iid)
                        self.db.record_exit(iid, -1)
                        del self.running_containers[iid]
                        continue
                    state = info.get("State", {})
                    if state.get("Running") is False:
                        exit_code = state.get("ExitCode", None)
                        logger.warning("container for instance %s exited code=%s", iid, exit_code)
                        self.db.record_exit(iid, exit_code)
                        # simple restart logic: rely on docker restart policy; if not set, apply DB restart policy
                        # if exceeded, disable instance
                        # here we simply remove from tracking so poll loop can restart if policy allows
                        del self.running_containers[iid]
                time.sleep(POLL_SECONDS)
            except Exception:
                logger.exception("error in poll loop")
                time.sleep(POLL_SECONDS)

def _sigterm(signum, frame):
    reactor.stop()
    sys.exit(0)

if __name__ == "__main__":
    reactor = Reactor()
    signal.signal(signal.SIGTERM, _sigterm)
    signal.signal(signal.SIGINT, _sigterm)
    reactor.start()
    # block until stop
    try:
        while not reactor.stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        reactor.stop()
