import threading
from threading import Event
from threading import Timer
import sys
import queue
import time
from os.path import dirname, realpath, sep, pardir
# Get current main.py directory
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DButils")
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")


from dbActions import dbNodesActions
from dbActions import dbDevicesActions
from nodeDiscoveryTool import nodeDeviceDiscoveryTool
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
        self.dbNodesActions.initConector(self.dbUser,self.dbPass,self.dbHost,self.dbName)
        self.dbActionMeasures.initConnector(self.dbUser,self.dbPass,self.dbHost,self.dbName)
        self.stop_event = Event()
        taskListen = threading.Thread(target=self._updateBaseDevices, args=())
        taskListen.start()
        self.CurrentNodes = self.dbAct.getNodes() # first start
        self.pendingNodes = [] #array of nodes pending to be processed
        pass

    def _updateBaseDevices(self):
        while not self.stop_event.is_set():
            self.CurrentNodes = self.dbNodesActions.getNodes()
            self.CurrentDevices = self.dbDevicesActions.getDevices()
            self.pendingNodes = []
            time.sleep(1)
            pass
        self.dbDevicesActions.deinitConnector()
        self.dbNodesActions.deinitConnector()
        pass

    def getNodeFromName(self, name):
        for node in self.CurrentNodes:
            if node.nodeName == name:
                return node
        return None
    
    def isNodePending(self, name):
        return (name in self.pendingNodes)
    
    '''
    {
        "Name":"MenyGardenNode1",
        "RootName":"/MenyGardenNode1/",
        "ip": "x.x.x.x"
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
                "Channel":""/MenyNode1/WatterSolenoid/state"",
                "Value": "ON"
            }
        ]

    }
    '''

    def updateNode(self, nodeData):
        nodeId = self.getNodeFromName(nodeData["Name"])
        if self.getNodeFromName(nodeData["Name"]) and self.isNodePending(nodeData["Name"]):
            nodeId = self.dbNodesActions.addNewNode(.....) ###### pending
            self.pendingNodes.add(nodeData.Name)
            pass

        for device in nodeData["Devices"]:
            logger.info("processing registered device %s" % device)
            if self.dbDevicesAct.deviceExists(device["Name"], nodeId):
                try:
                    result = self.dbDevicesAct.deviceChanged(device["Name"],device["Mode"],device["Type"],device["Channel"],nodeId)
                    self._updateDeviceMeasure(device["Value"] , self.getDeviceByNameNode(nodeId, device["Name"]))
                    if result[1]:
                        logger.info("device args updated")
                        self.dbDevicesAct.updateDevice(device["Name"],device["Mode"],device["Type"],device["Channel"],nodeId)
                except:
                    logger.error("device could not be updated: '" + str(device["Name"])+"'")
            else:
                try:
                    logger.info("new device added")
                    self.dbDevicesAct.addNewDevice(device["Name"],device["Mode"],device["Type"],device["Channel"],nodeId)
                except:
                    logger.error("device could not be registered: '" + str(device["Name"])+"'")
        pass

    def _updateDeviceMeasure(self, value, idDevice):
        try:
            logger.info("new measure for %s" % (value, idDevice))
            self.dbActionMeasures.addDeviceMeasure(value, idDevice)
        except Exception as e:
            print("Error attempting to update '" + str(idDevice) + "' device with '"+ str(value) +"' value")
        pass
    
    def __delete__(self):
        self.stop_event()
        pass



#Handles device requests by hearing messages over topic /inbound
# creates devices in the db if not exists
# updates its db measurement states
# notifies device manager from new devices to add by zmq
class deviceDataUpgrader():
    def __init__(self, initArgs):
        logger.info("init device message handler %s" % initArgs)
        self.dbHost = initArgs[0]
        self.dbName = initArgs[1]
        self.dbUser = initArgs[2]
        self.dbPass = initArgs[3]
        self.dbDevicesActions = dbDevicesActions()
        self.dbNodesActions = dbNodesActions()

        self.dbDevicesActions.initConnector(self.dbUser,self.dbPass,self.dbHost,self.dbName)
        self.dbNodesActions.initConector(self.dbUser,self.dbPass,self.dbHost,self.dbName)
        self.dbActionMeasures.initConnector(self.dbUser,self.dbPass,self.dbHost,self.dbName)
    
    # manages the main message threading
    def handle(self):
        pass

    #handle each device call to main register thread
    def _handleIncomingMessage(self, request):
        pass

    def _registerNodes(self):
        logger.info("retriving registered nodes")
        #attempts to register discovered nodes based on current information
        for nodeDObj in self.nodesDiscoveryObjs:
            for device in nodeDObj.devicesFound:
                logger.info("processing registered device %s" % device)
                if self.dbDevicesAct.deviceExists(device["Name"],nodeDObj.idNode):
                    try:
                        result = self.dbDevicesAct.deviceChanged(device["Name"],device["Mode"],device["Type"],device["Channel"],nodeDObj.idNode)
                        if result[1]:
                            logger.info("device args updated")
                            self.dbDevicesAct.updateDevice(device["Name"],device["Mode"],device["Type"],device["Channel"],nodeDObj.idNode)
                    except:
                        logger.error("device could not be updated: '" + str(device["Name"])+"'")
                else:
                    try:
                        logger.info("new device added")
                        self.dbDevicesAct.addNewDevice(device["Name"],device["Mode"],device["Type"],device["Channel"],nodeDObj.idNode)
                    except:
                        logger.error("device could not be registered: '" + str(device["Name"])+"'")
        self.dbDevicesAct.deinitConnector()
        pass




class nodeDeviceManager():
    def getNodes(self,nodeDeviceManagerArgs, timeoutInterval = 15):
        logger.info("get nodes started with %s %s", nodeDeviceManagerArgs, timeoutInterval)
        self.nodeDeviceManagerArgs = nodeDeviceManagerArgs
        self.timeoutInterval = timeoutInterval
        self.dbAct = dbNodesActions()
        self.state = "BUSY"
        self.dbAct.initConnector(user = nodeDeviceManagerArgs[2], password = nodeDeviceManagerArgs[3], host = nodeDeviceManagerArgs[0], database = nodeDeviceManagerArgs[1])
        self.CurrentNodes = self.dbAct.getNodes()
        self.dbAct.deinitConnector()
    
    def getState(self):
        return self.state
    
    def discoverNodeDevices(self):
        logger.info("starting device discovery")
        self.nodesDiscoveryObjs = []
        for node in self.CurrentNodes:
            nodeDiscoverObj = nodeDeviceDiscoveryTool()
            nodeDiscoverObj.initNodeParameters(node, self.nodeDeviceManagerArgs[4])
            self.nodesDiscoveryObjs.append(nodeDiscoverObj)
            pass
        self.stop_event = Event()
        taskListen = threading.Thread(target=self.taskWaitForDiscovery, args=())
        taskListen.start()
        
    
    def taskWaitForDiscovery(self):
        logger.info("waiting for discovery")
        self.timeoutTimer = Timer(self.timeoutInterval, self.stop)
        self.timeoutTimer.start()
        flagDone = 1
        while flagDone == 1 and not self.stop_event.is_set():
            flagDone = 0
            for nodeDObj in self.nodesDiscoveryObjs:
                if nodeDObj.getState() == 'WAIT':
                    flagDone = 1
                pass
            pass
        self.timeoutTimer.cancel()
        self.state = "DONE"
    
    def stop(self):
        logger.info("node device manager stopped")
        self.stop_event.set()
        for dNode in self.nodesDiscoveryObjs:
            dNode.stop()

    #{"Name":"Humidity","Mode":"PUBLISHER","Type":"FLOAT","Channel":"/MenyNode1/Humidity","Value":"40.00"}
    def registerNodes(self):
        logger.info("retriving registered nodes")
        #attempts to register discovered nodes based on current information
        self.dbDevicesAct = dbDevicesActions()
        self.dbDevicesAct.initConnector(user = self.nodeDeviceManagerArgs[2], password = self.nodeDeviceManagerArgs[3], host = self.nodeDeviceManagerArgs[0], database = self.nodeDeviceManagerArgs[1])
        for nodeDObj in self.nodesDiscoveryObjs:
            for device in nodeDObj.devicesFound:
                logger.info("processing registered device %s" % device)
                if self.dbDevicesAct.deviceExists(device["Name"],nodeDObj.idNode):
                    try:
                        result = self.dbDevicesAct.deviceChanged(device["Name"],device["Mode"],device["Type"],device["Channel"],nodeDObj.idNode)
                        if result[1]:
                            logger.info("device args updated")
                            self.dbDevicesAct.updateDevice(device["Name"],device["Mode"],device["Type"],device["Channel"],nodeDObj.idNode)
                    except:
                        logger.error("device could not be updated: '" + str(device["Name"])+"'")
                else:
                    try:
                        logger.info("new device added")
                        self.dbDevicesAct.addNewDevice(device["Name"],device["Mode"],device["Type"],device["Channel"],nodeDObj.idNode)
                    except:
                        logger.error("device could not be registered: '" + str(device["Name"])+"'")
        self.dbDevicesAct.deinitConnector()
        pass
        
            
        

#if __name__ == "__main__":

#    try:
#        # dbAct = dbNodesActions()
#        # dbAct.initConnector(host = '', database = '', user = '', password='')
#        # records = dbAct.getNodes();
#        # dbAct.deinitConnector()
#        args = ['','','','','']
#        devMgr = nodeDeviceManager()
#        devMgr.getNodes(args)
#        devMgr.discoverNodeDevices()
        
        
#        print("\nPrinting each row")
#        for row in records:
#            print("Id = ", row[0], )
#            print("Name = ", row[1])
#            print("Path  = ", row[2])
#            print("Protocol = ", row[3], "\n")

#    except:
#        print("Error reading data from MySQL table", e)
#    finally:
#        pass
#    pass