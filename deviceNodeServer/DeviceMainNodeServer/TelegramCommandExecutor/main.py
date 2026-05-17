# main.py (Telegram executor service entry)
import sys
import os
import time
import json
from threading import Event
import signal

from os.path import dirname, realpath, sep, pardir
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DButils")
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")

from telegramCommands import TelegramCommandExecutor
from secretReader import get_secret
from loggerUtils import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    args = [
        os.getenv("DB_HOST", ""),
        os.getenv("DB_NAME", ""),
        os.getenv("DB_USER", ""),
        get_secret("DB_PASSWORD")
    ]

    zmqDeviceManager = os.getenv("DEVICE_MANAGER_LOCAL_CONN", "")
    zmqVideoHandler = os.getenv("VIDEO_HANDLER_LOCAL_CONN", "")

    logger.info("Telegram Executor started with:")
    logger.info(args)
    logger.info(zmqDeviceManager)
    logger.info(zmqVideoHandler)

    zmqPaths = {
        'devices': zmqDeviceManager,
        'cameras': zmqVideoHandler
    }

    executor = TelegramCommandExecutor(args, zmqPaths)
    executor.start()

    eventStop = Event()
    def sigterm_handler(signum, frame):
        logger.info("stop process")
        eventStop.set()
        executor.stop()

    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    # Wait until signaled to stop
    try:
        while not eventStop.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("keyboard interrupt received, shutting down")
        executor.stop()
