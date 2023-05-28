from dbActions import dbNodesActions
from nodeManager import nodeDeviceManager
from deviceManager import deviceManager
from websocketHandler import wSocketServerManager
from configsCreate import configsParser
from videoHttpController import videoHandler
from telegramCommands import TelegramCommandExecutor
import threading
import time
import json


class serverManager():
	def init(self, args):
		#iniciar tareas principales
		#
		self.args = args
		
		self.taskLoopSearch = threading.Thread(target=self.startLoopSearch, args=(args,20,))
		self.taskLoopSearch.start()
		
		self.taskDeviceManager = threading.Thread(target=self.startDeviceManager, args=(args, 10,))
		self.taskDeviceManager.start()
		self.taskVideoServer = threading.Thread(target=self.startVideoServer, args=(args, ))
		self.taskVideoServer.start()

		time.sleep(10)
		#self.taskWSocketServer = threading.Thread(target=self.startWebSocketServer, args=(args, self.deviceManager.executeCMDJson))
		#self.taskWSocketServer.start()
		#ToDo: review exception, deviceManager is not being created
		self.taskTelegramServer = threading.Thread(target=self.startTelegramServer, args=(args, ))
		self.taskTelegramServer.start()
		self.startWebSocketServer(args, self.deviceManager.executeCMDJson)
		#self.startWebSocketServer.start()
		
		pass
	
	def startLoopSearch(self, args, timePoll):
		devMgr = nodeDeviceManager()
		while(True):
			devMgr.getNodes(args)
			devMgr.discoverNodeDevices()
			
			while devMgr.getState() != 'DONE':
				pass
			devMgr.registerNodes()
			time.sleep(timePoll)
		pass
	
	def startWebSocketServer(self, args, on_MessageCmd, socketPort = 8112):
		self.WSServer = wSocketServerManager()
		self.WSServer.init(socketPort)
		self.WSServer.serverListen(on_MessageCmd)
		pass
	
	def startDeviceManager(self, args, timePoll):
		deviceMgr = deviceManager()
		deviceMgr.init(args)
		self.deviceManager = deviceMgr
		
		while(True):
			deviceMgr.deviceLoad()
			time.sleep(timePoll)
			pass
		pass
	
	def startVideoServer(self, args):
		self.videoHandlerObj = videoHandler(args)
		self.videoHandlerObj.serverListen()
		pass
    
	def startTelegramServer(self, args):
		#init video server
		objInstances = {
			"devices":self.deviceManager,
			"cameras":self.videoHandlerObj
		}
		self.objTelegramServer = TelegramCommandExecutor(args, objInstances)
		self.objTelegramServer.fetchUserTokens()
		#expect a better approach since its not suitable to add every device each thread
		self.objTelegramServer.start()
		
		pass


if __name__ == "__main__":
    cfgObj = configsParser()
    args = cfgObj.readConfigData()
    objMainServer = serverManager()
    objMainServer.init(args)

    while(True):
        pass
    #deviceMgr = deviceManager()
    #deviceMgr.init(args)
    #objCmd['idDevice'], objCmd['command'], objCmd['args']
    #payload = json.dumps({'idDevice':5,'command':'hola','args':''})
    #deviceMgr.executeCMDJson(payload)
    #payload2 = json.dumps({'idDevice':7,'command':'','args':''})
    #deviceMgr.executeCMDJson(payload2)
    #app = tornado.web.Application(handlers=[(r"/workHandler", SocketHandler)],debug = True, template_path = os.path.join(os.path.dirname(__file__), "templates"),static_path = os.path.join(os.path.dirname(__file__), "static"))
    #app.init(self.deviceManager.executeCMDJson) #colocar el metodo de ejecutar comando
    #app.listen(8112)
    #tornado.ioloop.IOLoop.instance().start()
    # dbAct = dbNodesActions()
    # dbAct.initConnector(host =, database = , user = , password=)
    # records = dbAct.getNodes();
    # dbAct.deinitConnector()
    #
    #devMgr = nodeDeviceManager()
    #devMgr.getNodes(args)
    #devMgr.discoverNodeDevices()

    #while devMgr.getState() != 'DONE':
    #    pass
    #devMgr.registerNodes()

    #deviceMgr = deviceManager()
    #deviceMgr.init(args)
    #print("\nPrinting each row")
    #for row in records:
    #    print("Id = ", row[0], )
    #    print("Name = ", row[1])
    #    print("Path  = ", row[2])
    #    print("Protocol = ", row[3], "\n")


    #print("Error reading data from MySQL table", e)

    pass