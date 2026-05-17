#contains the logic for the telegram api telemetry
# telegramCommands.py
# Runs Telegram bots in separate processes to allow run_polling() to register signal handlers.
from multiprocessing import Process
import os
import sys
import time
import zmq
import json
import logging

from os.path import dirname, realpath, sep, pardir
# ensure local modules are importable
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DButils")
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")

from dbActions import dbUserActions
from loggerUtils import get_logger
from telegramBotUtil import run_bot_process  # function executed inside child process

logger = get_logger(__name__)

class TelegramCommandExecutor():
    """
    Manages Telegram bot processes. For each user token we spawn a child process
    that runs a TelegramBotUtil instance and calls run_polling() in that process.
    """

    def __init__(self, initArgs, zmqPaths):
        """
        initArgs: [dbHost, dbName, dbUser, dbPass]
        zmqPaths: dict with keys 'devices' and 'cameras' containing ZMQ connection strings
        """
        self.dbHost = initArgs[0]
        self.dbName = initArgs[1]
        self.dbUser = initArgs[2]
        self.dbPass = initArgs[3]
        self.activeUserProcesses = []  # list of (Process, token)
        self.zmqPaths = zmqPaths
        logger.info("init new telegram command executor instance")

    def start(self):
        userTks = self.fetchUserTokens()
        logger.info("starting telegram command executor")
        for token_row in userTks:
            token = token_row[0]
            logger.info("init user " + str(token))
            self.initNewUserApi(token)

    def stop(self):
        logger.info("stopping telegram command executor")
        # terminate child processes gracefully
        for proc, token in self.activeUserProcesses:
            try:
                if proc.is_alive():
                    logger.info(f"terminating bot process for token (truncated): {str(token)[:8]}")
                    proc.terminate()
                    proc.join(timeout=5)
                    if proc.is_alive():
                        logger.info("process still alive after terminate; killing")
                        proc.kill()
            except Exception as e:
                logger.error("error stopping user process: " + str(e))
        self.activeUserProcesses = []

    def fetchUserTokens(self):
        logger.info("retrieving user tokens")
        self.dbActions = dbUserActions()
        self.dbActions.initConnector(self.dbUser, self.dbPass, self.dbHost, self.dbName)
        userTks = self.dbActions.getUserTelegramTokens()
        return userTks

    def initNewUserApi(self, token):
        if token is None:
            logger.info('empty token')
            return
        """
        Spawn a new process that runs a Telegram bot for the given token.
        The child process will create its own ZMQ connections using the configured paths.
        """
        logger.info("telegram command executor new api user (spawning process)")
        # Build args for child process
        devices_zmq = self.zmqPaths.get('devices', '')
        cameras_zmq = self.zmqPaths.get('cameras', '')

        # Start a new process that runs the bot loop
        proc = Process(target=run_bot_process, args=(token, devices_zmq, cameras_zmq))
        proc.daemon = False
        proc.start()

        self.activeUserProcesses.append((proc, token))
        logger.info(f"spawned bot process pid={proc.pid} for token (truncated): {str(token)[:8]}")
