# zmq_integration.py
import threading
import logging
import zmq
import asyncio
from typing import Callable, Any

logger = logging.getLogger(__name__)

def init_mq_server(zmq_cfg: str):
    """
    Create and bind a REP socket. Returns (context, socket).
    Caller is responsible for closing/terminating on shutdown.
    """
    logger.info("video handler init mq server with: %s", zmq_cfg)
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(zmq_cfg)
    # optional: set socket.RCVTIMEO to avoid blocking forever (ms)
    # socket.RCVTIMEO = 1000
    return context, socket

def _mq_worker_loop(socket: zmq.Socket,
                    stop_event: threading.Event,
                    loop: asyncio.AbstractEventLoop,
                    async_handler: Callable[[dict], Any],
                    poll_timeout_ms: int = 1000,
                    handler_timeout_s: float = 5.0):
    """
    Thread target: poll the socket, receive requests, call async_handler in the event loop,
    and send replies. Uses poll to periodically check stop_event.
    - async_handler: coroutine function taking the request (dict) and returning a serializable reply.
    """
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    logger.info("ZMQ worker thread started")
    try:
        while not stop_event.is_set():
            socks = dict(poller.poll(poll_timeout_ms))
            if socket in socks and socks[socket] == zmq.POLLIN:
                try:
                    # adapt to your message format: recv_json / recv_string / recv
                    req = socket.recv_json(flags=0)
                except Exception as e:
                    logger.exception("Failed to recv request: %s", e)
                    # try to reply with error or continue
                    try:
                        socket.send_json({"error": "recv_failed"})
                    except Exception:
                        pass
                    continue

                # If no async handler provided, reply with simple ack
                if async_handler is None:
                    try:
                        socket.send_json({"ok": True})
                    except Exception:
                        logger.exception("Failed to send reply")
                    continue

                # Call the async handler in the event loop and wait for result
                try:
                    fut = asyncio.run_coroutine_threadsafe(async_handler(req), loop)
                    # wait for handler result with timeout
                    result = fut.result(timeout=handler_timeout_s)
                except asyncio.TimeoutError:
                    logger.exception("Async handler timed out")
                    try:
                        socket.send_json({"error": "handler_timeout"})
                    except Exception:
                        logger.exception("Failed to send timeout reply")
                except Exception as e:
                    logger.exception("Async handler raised: %s", e)
                    try:
                        socket.send_json({"error": "handler_exception", "detail": str(e)})
                    except Exception:
                        logger.exception("Failed to send exception reply")
                else:
                    # send the handler result back to requester
                    try:
                        socket.send_json(result)
                    except Exception:
                        logger.exception("Failed to send reply")
            # else: poll timed out, loop again and check stop_event
    finally:
        logger.info("ZMQ worker thread exiting")
        # best-effort cleanup here (socket/context closed by caller)
    return

def start_mq_thread(zmq_cfg: str,
                    loop: asyncio.AbstractEventLoop,
                    async_handler: Callable[[dict], Any] = None):
    """
    Helper to create context/socket and start the worker thread.
    Returns (context, socket, stop_event, thread).
    """
    context, socket = init_mq_server(zmq_cfg)
    stop_event = threading.Event()
    thread = threading.Thread(
        target=_mq_worker_loop,
        args=(socket, stop_event, loop, async_handler),
        daemon=True,
    )
    thread.start()
    return context, socket, stop_event, thread
