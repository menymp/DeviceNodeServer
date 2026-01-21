import threading
from threading import Event
from threading import Timer
import sys
from os.path import dirname, realpath, sep, pardir
# Get current main.py directory
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DBUtils")
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")


from dbActions import dbNodesActions
from dbActions import dbDevicesActions
from nodeDiscoveryTool import nodeDeviceDiscoveryTool
from loggerUtils import get_logger
logger = get_logger(__name__)

class nodeDeviceManager():
    def getNodes(self,nodeDeviceManagerArgs, timeoutInterval = 15):
        logger.info("get nodes started with %s" % (nodeDeviceManagerArgs, timeoutInterval))
        self.nodeDeviceManagerArgs = nodeDeviceManagerArgs
        self.timeoutInterval = timeoutInterval
        self.dbAct = dbNodesActions()
        self.state = "BUSY"
        self.dbAct.initConnector(user = nodeDeviceManagerArgs[2], password = nodeDeviceManagerArgs[3], host = nodeDeviceManagerArgs[0], database = nodeDeviceManagerArgs[1])
        self.CurrentNodes = self.dbAct.getNodes();
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