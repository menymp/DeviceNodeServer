# telegramBotUtil.py
# Child-process bot runner. This module is imported in both parent and child,
# but run_bot_process is executed inside the child process and creates its own
# TelegramBotUtil instance and ZMQ connections.

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from functools import partial
import logging
import sys
import os
import json
import cv2
import numpy as np
import requests
import io
import asyncio

from os.path import dirname, realpath, sep, pardir
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DButils")

from loggerUtils import get_logger
from dbActions import dbUserActions

logger = get_logger(__name__)

def build_pretty_envelope(commands_list, method_name="executeCMDJson"):
    """
    Build the exact envelope where `args` is a pretty-printed JSON array encoded
    as a string with CRLF newlines (\r\n), matching the format you requested.

    commands_list: Python list of dicts, e.g. [{"idDevice":12,"command":"ON","args":""}]
    Returns: a bytes payload ready to send over ZMQ (utf-8)
    """
    # 1) Pretty-print the commands array with 4-space indent
    pretty = json.dumps(commands_list, indent=4, ensure_ascii=False)

    # 2) Convert LF to CRLF to match the requested \r\n representation
    pretty_crlf = pretty.replace("\n", "\r\n")

    # 3) Build the outer envelope where args is the pretty string
    envelope = {
        "method": method_name,
        "args": pretty_crlf
    }

    # 4) Serialize the envelope compactly (this will escape the CRLF and quotes inside args)
    payload = json.dumps(envelope, separators=(',', ':'), ensure_ascii=False)

    return payload.encode('utf-8')

# Local ZMQ helper class used inside child processes
# Put this in a small helper module telegramCommands_helpers.py or inline here.
class HandleOnCmdLocal:
    def __init__(self, zmqPath):
        import zmq
        self.zmqPath = zmqPath
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.RCVTIMEO, 10000)
        self.socket.setsockopt(zmq.SNDTIMEO, 10000)
        if zmqPath:
            self.socket.connect(zmqPath)
            logger.info("HandleOnCmdLocal connected to " + zmqPath)

    def execCommand(self, cmd_list):
        """
        cmd_list: Python list of dicts, e.g. [{"idDevice":12,"command":"ON","args":""}]
        This method builds the pretty envelope where args is a pretty-printed JSON array
        encoded as a string with CRLF newlines, then sends it once over ZMQ.
        """
        try:
            payload_bytes = build_pretty_envelope(cmd_list, method_name="executeCMDJson")
            # send the single payload
            logger.info("running command " + str(payload_bytes))
            self.socket.send(payload_bytes)
            resp = self.socket.recv().decode()
            return resp
        except Exception as e:
            logger.error("HandleOnCmdLocal execCommand error: " + str(e))
            return None

    def getJpg(self, cmd_list):
        try:
            payload_bytes = build_pretty_envelope(cmd_list, method_name="executeCMDJson")
            # send the single payload
            logger.info("image req" + str(payload_bytes))
            self.socket.send(payload_bytes)
            md = self.socket.recv_json(flags=0)
            logger.info("received md: %s", md)
            raw = self.socket.recv(flags=0)
            
            dtype = np.dtype(md['dtype'])
            shape = tuple(md['shape'])

            arr = np.frombuffer(raw, dtype=dtype)
            arr = arr.reshape(shape)
            
            #msg = self.socket.socket.recv()
            #image = np.frombuffer(msg, dtype=md['dtype']).reshape(md['shape'])
            return arr
        except Exception as e:
            logger.error("HandleOnCmdLocal execCommand error: " + str(e))
            return None

# Entry point used by parent process to spawn a child process
def run_bot_process(token, devices_zmq, cameras_zmq):
    """
    This function runs inside the child process. It creates a TelegramBotUtil
    instance and calls run() which blocks on run_polling().
    """
    # Reconfigure logging in child process if necessary
    child_logger = get_logger(__name__ + ".child")
    child_logger.info("child process starting for token (truncated): " + str(token)[:8])
    bot = TelegramBotUtil(token, devices_zmq, cameras_zmq)
    try:
        bot.run()
    except Exception as e:
        child_logger.error("bot.run() exited with error: " + str(e))
    finally:
        child_logger.info("child process exiting for token (truncated): " + str(token)[:8])

class TelegramBotUtil():
    """
    Wrapper around python-telegram-bot Application.
    This class is intended to be instantiated and run inside a child process.
    """

    def __init__(self, token, devices_zmq, cameras_zmq):
        logger.info("init new telegram bot instance")
        self.token = token
        self.definedHandlers = []
        self.devices_zmq = devices_zmq
        self.cameras_zmq = cameras_zmq
        self.app = None

    def addHandlers(self, handlerList):
        self.definedHandlers = handlerList

    def addHandler(self, handler, command, refArg):
        # refArg is a callable or object created inside the child process
        self.app.add_handler(CommandHandler(command, partial(handler, refArg=refArg)))

    def run(self):
        if not self.token:
            logger.error("no token provided to TelegramBotUtil.run()")
            return False

        logger.info("token available, running bot (run_polling will block in this process)")
        # Build application
        self.app = ApplicationBuilder().token(self.token).build()

        # Create local handler objects that are safe inside this process
        # refArg objects are created here: create ZMQ proxies for devices and cameras
        ref_devices = None
        ref_cameras = None
        try:
            # Lazy import of handleOnCmd to avoid cross-process issues
            ref_devices = HandleOnCmdLocal(self.devices_zmq) if self.devices_zmq else None
            ref_cameras = HandleOnCmdLocal(self.cameras_zmq) if self.cameras_zmq else None
        except Exception as e:
            logger.warning("could not create local ZMQ handlers: " + str(e))

        # Define handlers and attach them
        # Handlers are module-level functions defined below
        handlers = [
            ('hello', hello, None),
            ('devices', deviceCmdHandler, ref_devices),
            ('cameras', videoCmdHandler, ref_cameras)
        ]

        for h in handlers:
            cmd = h[0]
            func = h[1]
            ref = h[2]
            self.addHandler(func, cmd, ref)

        # run_polling blocks and handles signals in this process
        self.app.run_polling()

    def stop(self):
        # Attempt to stop the application gracefully if called inside the same process
        try:
            if self.app:
                # Application.stop is a coroutine; ensure it's awaited properly
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.app.stop())
                else:
                    asyncio.run(self.app.stop())
            logger.info("stopping server")
            return True
        except Exception as e:
            logger.error("error stopping server: " + str(e))
            return False


### parser utils
def parse_device_command_text(text: str):
    """
    Parse a user command string into a list of command dicts suitable for execCommand.

    Syntax:
      /devices <idDevice> <server|device> <command> [args...]

    - idDevice: positive integer
    - scope: 'server' or 'device'
    - command: non-empty string
    - args: optional; if it starts with '{' or '[' it will be parsed as JSON, otherwise treated as a plain string

    Returns:
      (True, [cmd_obj, ...]) on success
      (False, "error message") on validation error
    """
    if not text or not text.strip():
        return False, "empty_command"

    # Normalize and split: allow the user to include or omit the leading "/devices"
    tokens = text.strip().split(None, 4)  # at most 5 parts: token, id, scope, cmd, args
    if len(tokens) == 0:
        return False, "invalid_command_format"

    first = tokens[0].lstrip('/')
    if first.lower() == 'devices':
        # expected form: devices id scope command [args]
        if len(tokens) < 4:
            return False, "usage: /devices <idDevice> <server|device> <command> [args]"
        _, id_raw, scope_raw, cmd_raw, *rest = tokens
        args_part = rest[0] if rest else ""
    else:
        # user omitted the leading token; treat tokens as id scope command [args]
        if len(tokens) < 3:
            return False, "usage: /devices <idDevice> <server|device> <command> [args]"
        id_raw, scope_raw, cmd_raw, *rest = tokens
        args_part = rest[0] if rest else ""

    # Validate idDevice
    try:
        idDevice = int(id_raw)
        if idDevice <= 0:
            return False, "idDevice must be a positive integer"
    except Exception:
        return False, "idDevice must be an integer"

    scope = scope_raw.lower()
    if scope not in ('server', 'device'):
        return False, "scope must be 'server' or 'device'"

    command_name = cmd_raw.strip()
    if not command_name:
        return False, "command name required"

    # Parse args: if it looks like JSON, parse it; otherwise keep as string
    parsed_args = ""
    if args_part:
        trimmed = args_part.lstrip()
        if trimmed.startswith('{') or trimmed.startswith('['):
            try:
                parsed_args = json.loads(args_part)
            except Exception:
                return False, "args must be valid JSON or a plain string"
        else:
            parsed_args = args_part

    # Build command object (do NOT JSON-stringify the whole object here)
    cmd_obj = {"idDevice": idDevice}
    if scope == 'server':
        cmd_obj["servercommand"] = command_name
    else:
        cmd_obj["command"] = command_name

    # Normalize args: keep as raw string if string, or keep dict/list if JSON
    if parsed_args == "":
        cmd_obj["args"] = ""
    elif isinstance(parsed_args, (dict, list)):
        # keep as Python object; the sender will json.dumps the whole payload once
        cmd_obj["args"] = parsed_args
    else:
        cmd_obj["args"] = str(parsed_args)

    return True, [cmd_obj]

# Helper functions and handlers that run in the child process

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE, refArg) -> None:
    logger.info("say hello")
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

# Updated handler to use the parser
async def deviceCmdHandler(update: Update, context: ContextTypes.DEFAULT_TYPE, refArg) -> None:
    """
    Telegram handler for /devices command. Uses parse_device_command_text and sends
    the resulting list of command objects to refArg.execCommand.
    """
    logger.info("device command handler requested")

    if refArg is None:
        await update.message.reply_text("Device service not available")
        return

    # Prefer full message text if available (user typed the whole command)
    text = ""
    if update.message and update.message.text:
        text = update.message.text
    else:
        # fallback to context.args (list of tokens)
        text = " ".join(context.args or [])

    ok, parsed = parse_device_command_text(text)
    if not ok:
        # parsed is an error string
        friendly = {
            "empty_command": "Empty command. Usage: /devices <idDevice> <server|device> <command> [args]",
            "invalid_command_format": "Invalid command format. Usage: /devices <idDevice> <server|device> <command> [args]",
            "idDevice must be a positive integer": "idDevice must be a positive integer",
            "idDevice must be an integer": "idDevice must be an integer",
            "scope must be 'server' or 'device'": "Scope must be 'server' or 'device'",
            "command name required": "Command name required",
            "args must be valid JSON or a plain string": "Args must be valid JSON or a plain string"
        }
        await update.message.reply_text(friendly.get(parsed, f"Invalid command: {parsed}"))
        return

    commands_array = parsed  # list of dicts

    # Ensure args field is a string for legacy handlers that expect string args.
    # If your device manager accepts JSON objects in args, skip this conversion.
    normalized = []
    for c in commands_array:
        c_copy = dict(c)  # shallow copy
        if isinstance(c_copy.get("args"), (dict, list)):
            # convert JSON args to compact string to preserve structure but avoid pretty printing
            c_copy["args"] = json.dumps(c_copy["args"], separators=(',', ':'))
        else:
            # ensure it's a plain string
            c_copy["args"] = "" if c_copy.get("args") is None else str(c_copy.get("args"))
        normalized.append(c_copy)

    try:
        # Pass the Python list to execCommand; the sender should json.dumps once.
        result = refArg.execCommand(normalized)
        logger.info("device command handler returned " + str(result))
        await update.message.reply_text(str(result))
    except Exception as e:
        logger.error("device command execution error: " + str(e))
        await update.message.reply_text("Error executing device command: " + str(e))


# Environment variable to configure the video HTTP API base URL
VIDEO_API_BASE_URL = os.getenv("VIDEO_API_BASE_URL", "http://localhost:9090")

def _build_camera_url(camera_id: str) -> str:
    """
    Build the URL to fetch the latest frame for a camera.
    Example: http://localhost:9090/latest/841FE8701120MenyEspCam1
    """
    base = VIDEO_API_BASE_URL.rstrip('/')
    return f"{base}/latest/{camera_id}"

def _fetch_image_bytes_sync(url: str, timeout: float = 5.0) -> bytes:
    """
    Blocking HTTP GET to fetch image bytes. Intended to be run in executor.
    Raises requests.RequestException on failure.
    """
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.content

def _decode_image_bytes(img_bytes: bytes):
    """
    Decode JPEG/PNG bytes into an OpenCV image (numpy array).
    Returns numpy.ndarray or None on failure.
    """
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img

async def _fetch_and_prepare_jpeg(camera_id: str, timeout: float = 5.0):
    """
    Async wrapper that fetches image bytes in a thread and returns JPEG bytes ready to send.
    Returns bytes (JPEG) or raises Exception.
    """
    url = _build_camera_url(camera_id)
    loop = asyncio.get_running_loop()

    # 1) fetch bytes in thread
    img_bytes = await loop.run_in_executor(None, _fetch_image_bytes_sync, url, timeout)

    # 2) decode in thread (cv2.imdecode is blocking)
    img = await loop.run_in_executor(None, _decode_image_bytes, img_bytes)
    if img is None:
        raise ValueError("failed to decode image from bytes")

    # 3) encode to JPEG in thread (so we send a compressed image to Telegram)
    def _encode_jpeg(image):
        ok, jpg = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            raise ValueError("jpeg encoding failed")
        return jpg.tobytes()

    jpeg_bytes = await loop.run_in_executor(None, _encode_jpeg, img)
    return jpeg_bytes

async def videoCmdHandler(update: Update, context: ContextTypes.DEFAULT_TYPE, refArg) -> None:
    """
    Handler for /cameras or /video commands.
    - 'ls' returns the list via refArg.execCommand
    - 'get <cameraId>' fetches the latest frame from the HTTP API and sends it to Telegram
    """
    logger.info("video command handler requested %s", str(context.args))

    if refArg is None:
        await update.message.reply_text("Video service not available")
        return

    args = context.args or []

    # handle list command
    if 'ls' in args:
        try:
            result = refArg.execCommand(args)
            if result is None:
                await update.message.reply_text("No result from video service")
                return
            await update.message.reply_text(str(result))
        except Exception as e:
            logger.exception("video ls command error: %s", e)
            await update.message.reply_text("Error listing cameras: " + str(e))
        return

    # handle get command: find 'get' token and take the next token as camera id
    if 'get' in args:
        try:
            idx = args.index('get')
            if idx + 1 >= len(args):
                await update.message.reply_text("Usage: /devices get <cameraId>")
                return
            camera_id = args[idx + 1].strip()
            if not camera_id:
                await update.message.reply_text("Invalid camera id")
                return

            logger.info("getting image for camera %s", camera_id)

            # fetch and prepare jpeg bytes (runs blocking work in executor)
            try:
                jpeg_bytes = await _fetch_and_prepare_jpeg(camera_id, timeout=8.0)
            except requests.RequestException as re:
                logger.warning("failed to fetch image from camera %s: %s", camera_id, re)
                await update.message.reply_text(f"Failed to fetch image from camera {camera_id}: {re}")
                return
            except Exception as e:
                logger.exception("error preparing image for camera %s: %s", camera_id, e)
                await update.message.reply_text(f"Failed to prepare image: {e}")
                return

            # send JPEG to Telegram using an in-memory BytesIO
            img_io = io.BytesIO(jpeg_bytes)
            img_io.name = f"{camera_id}.jpg"
            img_io.seek(0)

            chat_id = update.message.chat_id
            await context.bot.send_photo(chat_id=chat_id, photo=img_io)
            logger.info("sent image for camera %s to chat %s", camera_id, chat_id)

        except Exception as e:
            logger.exception("unexpected error in video get handler: %s", e)
            await update.message.reply_text("Unexpected error: " + str(e))

        return

    # fallback: unknown subcommand
    await update.message.reply_text("Usage: /devices ls  OR  /devices get <cameraId>")



