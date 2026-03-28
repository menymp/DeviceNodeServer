# reactor/handler_runner.py
import argparse
import importlib
import inspect
import json
import logging
import signal
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("handler_runner")

stop_flag = False

def _on_sigterm(signum, frame):
    global stop_flag
    stop_flag = True

signal.signal(signal.SIGTERM, _on_sigterm)
signal.signal(signal.SIGINT, _on_sigterm)

def run_sync_handler(func, config):
    def send_output(obj):
        try:
            print(json.dumps(obj), flush=True)
        except Exception:
            logger.exception("failed to write output")
    try:
        func(config, lambda: stop_flag, send_output)
    except Exception:
        logger.exception("handler crashed")
        send_output({"status":"error","log":"handler crashed"})

async def run_async_handler(func, config):
    def send_output(obj):
        try:
            print(json.dumps(obj), flush=True)
        except Exception:
            logger.exception("failed to write output")
    try:
        await func(config, lambda: stop_flag, send_output)
    except Exception:
        logger.exception("async handler crashed")
        send_output({"status":"error","log":"async handler crashed"})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--entry", required=True, help="module.submodule:func")
    parser.add_argument("--config", required=True, help="JSON config")
    args = parser.parse_args()

    if ":" not in args.entry:
        logger.error("entry must be module:func")
        sys.exit(2)
    module_name, func_name = args.entry.split(":")
    module = importlib.import_module(module_name)
    func = getattr(module, func_name)

    try:
        config = json.loads(args.config)
    except Exception:
        config = {}

    if inspect.iscoroutinefunction(func):
        import asyncio
        asyncio.run(run_async_handler(func, config))
        return

    run_sync_handler(func, config)

if __name__ == "__main__":
    main()
