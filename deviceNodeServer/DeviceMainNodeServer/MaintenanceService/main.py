# Menymp 2026
# scheduler to perform maintenance tasks

import os
import time
import schedule
import sys

from os.path import dirname, realpath, sep, pardir
# Get current main.py directory
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DBUtils")
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")

from dbActions import dbDevicesActions
from secretReader import get_secret
from loggerUtils import get_logger
logger = get_logger(__name__)

class devicesDbMaintenance:
    def __init__(self, initArgs):
        logger.info("new devices Maintenance created with %s" % initArgs)
        self.dbActions = dbDevicesActions()
        self.dbHost = initArgs[0]
        self.dbName = initArgs[1]
        self.dbUser = initArgs[2]
        self.dbPass = initArgs[3]
        self.dbActions = dbDevicesActions()
        self.dbActions.initConnector(self.dbUser,self.dbPass,self.dbHost,self.dbName)
        pass

    def performMaintenance(self):
        logger.info("running maintenance")
        #by default 60 days of retention
        self.dbActions.cleanOldRecords()
        pass

    def __exit__(self):
        logger.info("maintenance exiting closing")
        self.dbActions.deinitConnector()
        pass



if __name__ == "__main__":
    args = [os.getenv("DB_HOST", ""), os.getenv("DB_NAME", ""), os.getenv("DB_USER", ""), get_secret("DB_PASSWORD_FILE")]

    # Set maintenance objects
    devicesMaintainer = devicesDbMaintenance(args)
    
    #set schedulers callbacks
    schedule.every(24).hours.do(devicesMaintainer.performMaintenance())

    logger.info("MaintenanceService started with:")
    logger.info(args)

    # Run forever
    while True:
        schedule.run_pending()
        time.sleep(60)

