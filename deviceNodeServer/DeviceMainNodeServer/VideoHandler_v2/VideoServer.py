# async_ingest_server.py
import asyncio
import struct
import json
import logging
from collections import deque
from datetime import datetime
from typing import Dict, Deque, Tuple
import argparse
import io
import os

# Optional HTTP endpoint
try:
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except Exception:
    AIOHTTP_AVAILABLE = False

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

#camera_store: CameraFrames = {}
camera_bytes: Dict[str, int] = {}  # bytes used per camera
global_bytes = 0
global_lock = asyncio.Lock()       # protect global_bytes and camera_bytes

# Helpers
def camera_id_from_header(hdr: dict) -> str:
    # prefer mac if present, else name
    mac = hdr.get("mac")
    name = hdr.get("name")
    if mac:
        return mac
    if name:
        return name
    # fallback to generated id
    return f"unknown_{hdr.get('camera_type','0')}"

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
            ts = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
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
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logging.info("HTTP API listening on %s:%d", host, port)

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default=LISTEN_HOST)
    p.add_argument("--port", type=int, default=LISTEN_PORT)
    p.add_argument("--http", action="store_true", help="enable HTTP API on port+1")
    return p.parse_args()

async def main():
    args = parse_args()
    tasks = [start_tcp_server(args.host, args.port)]
    if args.http:
        tasks.append(start_http_server(args.host, args.port + 1))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    asyncio.run(main())
