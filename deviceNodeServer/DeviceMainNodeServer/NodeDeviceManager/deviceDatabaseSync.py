import threading
from threading import Event
import sys
import time
from os.path import dirname, realpath, sep, pardir
# Get current main.py directory
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DButils")
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")


from dbActions import dbNodesActions
from dbActions import dbDevicesActions
from loggerUtils import get_logger
logger = get_logger(__name__)


#
# Periodicaly retrives the current nodes and its devices from database
#
class deviceDatabaseSync():
    def __init__(self, initArgs):
        logger.info("init device sync %s" % initArgs)
        self.dbHost = initArgs[0]
        self.dbName = initArgs[1]
        self.dbUser = initArgs[2]
        self.dbPass = initArgs[3]
        self.dbDevicesActions = dbDevicesActions()
        self.dbNodesActions = dbNodesActions()
        self.dbActionMeasures = dbDevicesActions()
        self.dbDevicesActions.initConnector(self.dbUser,self.dbPass,self.dbHost,self.dbName)
        self.dbNodesActions.initConnector(self.dbUser,self.dbPass,self.dbHost,self.dbName)
        self.dbActionMeasures.initConnector(self.dbUser,self.dbPass,self.dbHost,self.dbName)
        self._requestNodes()
        self.stop_event = Event()
        self.taskListen = threading.Thread(target=self._updateBaseDevices, args=())
        self.taskListen.start()
        self.pendingNodes = set() #array of nodes pending to be processed
        self.devicesValues = {}
        pass
    
    def _requestNodes(self):
        try:
            self.CurrentNodes = self.dbNodesActions.getNodes() # first start
            logger.info("Updated notes")
        except Exception as e:
            self.CurrentNodes = []
            logger.error("Failed to request nodes, retrying %s" % (e))

    def _updateBaseDevices(self):
        while not self.stop_event.is_set():
            self._requestNodes()
            self.CurrentDevices = self.dbDevicesActions.getDevices()
            self.pendingNodes = set()
            time.sleep(1)
            pass
        self.dbDevicesActions.deinitConnector()
        self.dbNodesActions.deinitConnector()
        pass

    def getNodeFromName(self, name):
        logger.info(self.CurrentNodes)
        for node in self.CurrentNodes:
            if node[2] == name:
                logger.info("found node ")
                return node
        logger.info("node not found %s" % (name))
        return None
    
    def nodeAcknowledge(self, name, mac_addr):
        # attempts to check if a node name is already used, if so, check if it mac is same
        node = self.getNodeFromName(name)
        if node is None or node[1] == mac_addr:
            return True
        else:
            return False
        
    
    def getDeviceInfo(self, deviceId):
        for device in self.CurrentDevices:
            if device[0] == deviceId:
                logger.info("found device ")
                return device
        logger.info("device not found %s" % (deviceId))
        return None
    
    def isNodePending(self, name):
        return (name in self.pendingNodes)
    
    '''
    {
        "Name":"MenyGardenNode1",
        "RootName":"/MenyGardenNode1/",
        "ip": "x.x.x.x",
        "Devices": [
            {
                "Name":"PirSensor",
                "Mode":"PUBLISHER",
                "Type":"STRING",
                "Channel": "/MenyGardenNode1/PirSensor",
                "Value": "69.69"
            },
            {
                "Name":"WaterPump",
                "Mode":"SUBSCRIBER",
                "Type":"STRING",
                "Channel":"/MenyNode1/WaterSolenoid/state",
                "Value": "ON"
            }
        ]

    }
    '''

    def updateNode(self, nodeData):
        nodeObj = self.getNodeFromName(nodeData["Name"])
        nodeId = nodeObj[0]
        logger.info('node ID: %s' % (nodeId))
        if not self.getNodeFromName(nodeData["Name"]) and not self.isNodePending(nodeData["Name"]):
            logger.info("adding new node %s", nodeData["Name"])
            nodeId = self.dbNodesActions.addNewNode(nodeData["Name"], nodeData["RootName"], nodeData["mac_addr"], 2)
            self.pendingNodes.add(nodeData["Name"])
            pass

        logger.info('Node id search: %s' % (nodeId))

        for device in nodeData["Devices"]:
            logger.info("processing registered device %s" % (device["Name"]))
            if self.dbDevicesActions.deviceExists(device["Name"], nodeId):
                try:
                    result = self.dbDevicesActions.deviceChanged(device["Name"],device["Mode"],device["Type"],device["Channel"],nodeId)
                    deviceId = self.dbDevicesActions.getDeviceByNameNode(nodeId, device["Name"])[0][0]
                    self._updateDeviceMeasure(device["Value"] , deviceId)
                    self.devicesValues[deviceId] = device["Value"]
                    if result[1]:
                        logger.info("device args updated")
                        self.dbDevicesActions.updateDevice(device["Name"],device["Mode"],device["Type"],device["Channel"],nodeId)
                except Exception as e:
                    logger.error("device could not be updated: '" + str(device["Name"])+"' " + str(e))
            else:
                try:
                    logger.info("new device added")
                    self.dbDevicesActions.addNewDevice(device["Name"],device["Mode"],device["Type"],device["Channel"],nodeId)
                except:
                    logger.error("device could not be registered: '" + str(device["Name"])+"'")
        pass

    def _updateDeviceMeasure(self, value, idDevice):
        try:
            logger.info("new measure for %s %s" % (value, idDevice))
            self.dbActionMeasures.addDeviceMeasure(value, idDevice)
        except Exception as e:
            print("Error attempting to update '" + str(idDevice) + "' device with '"+ str(value) +"' value")
        pass

    def getLastDeviceMeasure(self, idDevice):
        if idDevice in self.devicesValues:
            value = self.devicesValues[idDevice]
            logger.info("last device %s measure is: %s" % (idDevice, value))
            return value
        else:
            logger.info("no measurement for device %s" % idDevice)
            return None
    
    def __delete__(self):
        self.stop_event.set()
        self.taskListen.join()
        pass