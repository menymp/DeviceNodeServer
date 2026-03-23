# async_ingest_server.py
import asyncio
import struct
import json
import logging
from datetime import datetime
from typing import Dict, Deque, Tuple
import argparse
import io
import os
import signal
import socket
import time
from FrameServerConstructor import FrameServerConstructor
from zmqServerUtils import start_mq_thread
from WebUtils import *
from secretReader import get_secret
from loggerUtils import get_logger
from aiohttp import web
AIOHTTP_AVAILABLE = True

logger = get_logger(__name__)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Config
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 9000

# Memory limits
MAX_FRAMES_PER_CAMERA = 1            # keep last N frames per camera
MAX_BYTES_PER_CAMERA = 10 * 1024 * 1024  # 10 MB per camera
GLOBAL_MEMORY_LIMIT = 500 * 1024 * 1024  # 500 MB global cap

# Max allowed single frame size (safety)
MAX_SINGLE_FRAME = 20 * 1024 * 1024  # 20 MB

# Storage structures
# camera_store: cam_id -> (ts, hdr, bytes)
camera_store: Dict[str, Tuple[str, dict, bytes]] = {}

camera_bytes: Dict[str, int] = {}  # bytes used per camera
global_bytes = 0
global_lock = asyncio.Lock()       # protect global_bytes and camera_bytes

# Helpers
def camera_id_from_header(hdr: dict) -> str:
    # prefer mac if present, else name
    mac = hdr.get("mac")
    name = hdr.get("name")
    return mac + name

async def read_exact(reader: asyncio.StreamReader, n: int, timeout: float = 10.0) -> bytes:
    """Read exactly n bytes or raise asyncio.IncompleteReadError."""
    try:
        return await asyncio.wait_for(reader.readexactly(n), timeout)
    except asyncio.TimeoutError:
        raise asyncio.IncompleteReadError(partial=b"", expected=n)

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    peer = writer.get_extra_info("peername")
    logging.info("Connected %s", peer)
    try:
        while True:
            # 1) header length (4 bytes BE)
            hdr_len_b = await read_exact(reader, 4)
            (hdr_len,) = struct.unpack(">I", hdr_len_b)
            if hdr_len == 0 or hdr_len > 4096:
                logging.warning("Invalid header length %d from %s", hdr_len, peer)
                break

            # 2) header JSON
            hdr_bytes = await read_exact(reader, hdr_len)
            try:
                hdr = json.loads(hdr_bytes.decode("utf-8"))
            except Exception as e:
                logging.warning("JSON parse error from %s: %s", peer, e)
                break

            # 3) image length
            img_len_b = await read_exact(reader, 4)
            (img_len,) = struct.unpack(">I", img_len_b)
            if img_len == 0 or img_len > MAX_SINGLE_FRAME:
                logging.warning("Invalid image length %d from %s", img_len, peer)
                break

            # 4) image payload
            img_bytes = await read_exact(reader, img_len)

            # Validate header frame_size if present
            header_frame_size = hdr.get("frame_size")
            if header_frame_size is not None and int(header_frame_size) != img_len:
                logging.info("Header frame_size mismatch: header=%s actual=%s from %s", header_frame_size, img_len, peer)

            # Store in memory with limits
            cam_id = camera_id_from_header(hdr)
            ts = datetime.now().isoformat(timespec="milliseconds") + "Z"
            frameConstructor.processCameraHeader(hdr.get("type"), hdr.get("name"), hdr.get("mac"), hdr.get("ip_addr"))
            await store_frame_latest(cam_id, ts, hdr, img_bytes)

    except asyncio.IncompleteReadError:
        logging.info("Client %s disconnected", peer)
    except Exception as e:
        logging.exception("Error handling client %s: %s", peer, e)
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        logging.info("Connection closed %s", peer)

async def store_frame_latest(cam_id: str, ts: str, hdr: dict, img_bytes: bytes) -> bool:
    global global_bytes
    size = len(img_bytes)
    async with global_lock:
        if global_bytes + size > GLOBAL_MEMORY_LIMIT:
            logging.warning("Global memory cap reached: rejecting frame from %s (%d bytes)", cam_id, size)
            return False
        old = camera_store.get(cam_id)
        if old:
            old_size = len(old[2])
            global_bytes -= old_size
        camera_store[cam_id] = (ts, hdr, img_bytes)
        global_bytes += size
        return True


# Optional HTTP API to fetch latest frame for a camera (if aiohttp installed)
async def http_latest_frame(request):
    logger.debug("Request arrived")

    cam = request.match_info.get("cam")
    if cam not in camera_store:
        return web.Response(status=404, text="no frames")

    entry = camera_store[cam]

    # support both shapes: deque of tuples or single tuple (ts, hdr, img)
    if isinstance(entry, tuple) and len(entry) == 3:
        ts, hdr, img = entry
    else:
        # assume deque-like
        try:
            ts, hdr, img = entry[-1]
        except Exception:
            return web.Response(status=500, text="invalid frame storage format")

    headers = {
        "X-Camera-TS": ts,
        "X-Camera-Name": hdr.get("name", ""),
        "X-Camera-MAC": hdr.get("mac", ""),
        "Content-Type": "image/jpeg"
    }
    return web.Response(body=img, headers=headers)

# The validated handler
async def http_frame_Constructor(request: web.Request):
    try:
        # parse and validate simple numeric params
        height = parse_int(request.query.get("height"), "height", minimum=1, maximum=4000, required=False)
        width  = parse_int(request.query.get("width"),  "width",  minimum=1, maximum=4000, required=False)

        # idList: optional list of ints
        idList = parse_id_list(request, "idList")
        # optional rowLen (must be positive if provided)
        rowLen = parse_int(request.query.get("rowLen"), "rowLen", minimum=1, maximum=1000, required=False)

        # idText: optional boolean (default False)
        idText = parse_bool(request.query.get("idText"), default=False)


    except ValueError as e:
        return web.Response(status=400, text=str(e))
    
    buildArgs = {
        "height": height,
        "width": width,
        "idList": idList,
        "rowLen": rowLen,
        "idText": idText
    }

    frame = frameConstructor.getJpg(camera_store, buildArgs)

    if not frame:
        return web.Response(status=404, text="no frames")

    ts, hdr, img = frame

    headers = {
        "X-Camera-TS": ts,
        "X-Camera-Name": hdr.get("name", ""),
        "X-Camera-MAC": hdr.get("mac", ""),
        "Content-Type": "image/jpeg"
    }

    return web.Response(body=img, headers=headers)

# server helpers (tab indented)
async def start_tcp_server(host: str, port: int):
    server = await asyncio.start_server(handle_client, host, port, backlog=200)
    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    logging.info("TCP server listening on %s", addrs)
    async with server:
        await server.serve_forever()

async def start_http_server(host: str, port: int):
    if not AIOHTTP_AVAILABLE:
        logging.warning("aiohttp not available; HTTP API disabled")
        return
    app = web.Application()
    app.router.add_get("/latest/{cam}", http_latest_frame)
    app.router.add_get("/video_feed", http_frame_Constructor)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logging.info("HTTP API listening on %s:%d", host, port)


async def handle_mq_request(req: dict):
    """
    Async handler called from ZMQ thread.
    Perform DB lookups or other async work here.
    Req is the JSON-decoded request from the client.
    Return a JSON-serializable reply.
    """
    try:
        # Example: expect {"action":"get_camera","name":"cam1"}
        if req.get("method") != "execCommand":
            return {"error": "unknown command"}
        if req.get("args") is None:
            return {"error": "missing args"}


        #parses the command
        #list cameras
        #default generic object
        argsObj={
        	"height":600,
        	"width":600,
        	"idList":[], #expected ids to be concatenated
        	"rowLen":1, #how many images stack in the horizontal
        	"idText":True #enable video id for source
        }
        
        inTks = req.get("args").split(' ') # TODO TEST IT NOT SURE WHAT is the format
        if inTks[0] == 'ls':
            return str(frameConstructor.getDeviceIds())
        elif inTks[0] == "get":
            if len(inTks) == 2:
                argsObj["idList"].append(int(inTks[1]))
                result = frameConstructor.buildFrame(argsObj)
                return result
            else:
                return None
        else:
            return {"ok": False, "error": "exception", "detail": str(e)}
    except Exception as e:
        logger.exception("handle_mq_request failed")
        return {"ok": False, "error": "exception", "detail": str(e)}


frameConstructor = None

async def main():
    global frameConstructor
    args = [os.getenv("DB_HOST", ""), os.getenv("DB_NAME", ""), os.getenv("DB_USER", ""), get_secret("DB_PASSWORD")] # [argsP["host"],argsP["dbname"],argsP["user"],argsP["pass"],argsP["broker"]]
    zmqCfgConn = os.getenv("VIDEO_HANDLER_SERVER_PATH", "")
    httpVideoPort = int(os.getenv("VIDEO_SEED_PORT", ""))
    deviceServerPort = int(os.getenv("DEVICE_SOCKET_PORT", ""))
    logger.info("Configs received for video handler:")
    logger.info(args)
    logger.info(zmqCfgConn)
    logger.info(httpVideoPort)
    logger.info(deviceServerPort)

    
    frameConstructor = FrameServerConstructor(args)
    await frameConstructor.init()

    # start ZMQ thread (pass the running loop and async handler)
    loop = asyncio.get_running_loop()
    mq_context, mq_socket, mq_stop_event, mq_thread = start_mq_thread(zmqCfgConn, loop, handle_mq_request)
    logger.info("ZMQ thread started")

    stop_event = asyncio.Event()
    # create the periodic updater task (preferred)
    update_task = asyncio.create_task(frameConstructor.update_video_sources(stop_event, interval=2.0))
    # start servers and keep references

    tasks = [start_tcp_server(LISTEN_HOST, deviceServerPort)]
    tasks.append(start_http_server(LISTEN_HOST, httpVideoPort))
    #tasks.append(frameConstructor.update_video_sources(stop_event, interval=2.0))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    asyncio.run(main())

'''
    # start ZMQ thread (pass the running loop and async handler)
    loop = asyncio.get_running_loop()
    mq_context, mq_socket, mq_stop_event, mq_thread = start_mq_thread(zmqCfgConn, loop, handle_mq_request)
    logger.info("ZMQ thread started")

    # stop event for graceful shutdown
    stop_event = asyncio.Event()
    logger.info("a")

    # create the periodic updater task (preferred)
    update_task = asyncio.create_task(frameConstructor.update_video_sources(stop_event, interval=2.0))
    logger.info("B")
    # start servers and keep references
    tcp_server = await start_tcp_server(LISTEN_HOST, deviceServerPort)  # returns server object
    # create a task to run the server loop
    logger.info("B1")
    tcp_task = asyncio.create_task(tcp_server.serve_forever())
    logger.info("C")
    http_runner_site = None
    if AIOHTTP_AVAILABLE:
        runner, site = await start_http_server(LISTEN_HOST, httpVideoPort)
        http_runner_site = (runner, site)
    logger.info("D")
    # Now wait for shutdown signal
    loop = asyncio.get_running_loop()
    def _on_signal():
        logging.info("shutdown signal received")
        stop_event.set()
    try:
        loop.add_signal_handler(signal.SIGINT, _on_signal)
        loop.add_signal_handler(signal.SIGTERM, _on_signal)
    except NotImplementedError:
        pass
    logger.info("E")
    # Wait until stop_event is set
    await stop_event.wait()
    logging.info("shutting down")

    # Begin shutdown: cancel tasks and cleanup
    # 1) ask periodic loop to stop (we already set stop_event)
    # 2) cancel tasks to speed up shutdown
    update_task.cancel()
    tcp_task.cancel()

    # await tasks and collect exceptions so one failure doesn't block cleanup
    results = await asyncio.gather(update_task, tcp_task, return_exceptions=True)
    for r in results:
        if isinstance(r, Exception) and not isinstance(r, asyncio.CancelledError):
            logging.exception("Background task error: %s", r)

    # cleanup servers and resources
    if http_runner_site is not None:
        runner, site = http_runner_site
        await runner.cleanup()

    if tcp_server is not None:
        tcp_server.close()
        await tcp_server.wait_closed()

    # shutdown ZMQ thread: signal and join
    mq_stop_event.set()
    mq_thread.join(timeout=5.0)
    try:
        # close socket and terminate context (best-effort)
        mq_socket.close(linger=0)
        mq_context.term()
    except Exception:
        logger.exception("Error closing ZMQ socket/context")

    # close DB connector inside frameConstructor
    try:
        if frameConstructor.dbCamActions:
            await frameConstructor.dbCamActions.close()
    except Exception:
        logging.exception("Error closing DB connector")
'''
