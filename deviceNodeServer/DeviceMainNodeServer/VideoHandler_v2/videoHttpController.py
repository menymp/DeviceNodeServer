import time
import tornado.ioloop
import tornado.web
import tornado.httpserver
from threading import Threading, Event
import json
import asyncio
import sys

from os.path import dirname, realpath, sep, pardir
# Get current main.py directory
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DButils")
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")

from loggerUtils import get_logger
logger = get_logger(__name__)

from dbActions import dbVideoActions
from FrameServerConstructor import *

class videoFeedHandler(tornado.web.RequestHandler):
	def initialize(self, frameConstObj):
		logger.info("video handler controller started")
		self.frameConstObj = frameConstObj
	
	@tornado.gen.coroutine
	def get(self):
		logger.info("video handler controller accepting new client request")
		self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
		self.set_header( 'Pragma', 'no-cache')
		self.set_header( 'Content-Type', 'multipart/x-mixed-replace;boundary=--jpgboundary')
		self.set_header('Connection', 'close')
		
		my_boundary = "--jpgboundary"
		#ToDo: make this object pass as a parameter from get
		#ToDo: the following lines are ugly, i will fix it later, or never...
		#argsObj={"height":600,"width":600,"idList":[1,2,3],"rowLen":2,"idText":True}
		strArg = self.get_argument('vidArgs')
		argsObj = json.loads(strArg)
		argsObj = json.loads(argsObj)
		img = self.frameConstObj.getJpg(argsObj)
		
		
		self.write(my_boundary)
		self.write("Content-type: image/jpeg\r\n")
		self.write("Content-length: %s\r\n\r\n" % len(img))
		self.write(img)
		
		self.flush()


class videoHandler():
	def __init__(self, args):
		logger.info("init new video handler with: " + str(args))
		self.dbHost = args[0]
		self.dbName = args[1]
		self.dbUser = args[2]
		self.dbPass = args[3]
		self.dbCamActions = dbVideoActions()
		self.dbCamActions.initConnector(self.dbUser,self.dbPass,self.dbHost,self.dbName)
		
		self.frameObjConstructor = FrameServerConstructor()
		self.frameObjConstructor.start()

		self.stop_event = Event()
		self.app = self._make_app(self.frameObjConstructor)
		pass
	
	def execCommand(self, inputArgs):
		#parses the command
		#list cameras
		#default generic object
		argsObj={
			"height":600,
			"width":600,
			"idList":[], #expected ids to be concatenated
			"rowLen":1, #how many images stack in the horizontal
			"idText":True #enable video id for source
		}
		
		inTks = inputArgs
		if inTks[0] == 'ls':
			return str(self.frameObjConstructor.getDeviceIds())
		elif inTks[0] == "get":
			if len(inTks) == 2:
				argsObj["idList"].append(int(inTks[1]))
				result = self.frameObjConstructor.buildFrame(argsObj)
				return result
			else:
				return None
		else:
			return "unknown command"
		
	def _update_video_sources(self):
		while self.stop_event.is_set() == False:
			availableCameras = self.frameObjConstructor.get_cameras_info()
			for camera in availableCameras:
				cameraDbId = None
				exists, id = self.dbCamActions.videoSourceExists_v2(camera["name"], camera["mac"])
				if exists:
					self.dbCamActions.updateVideoSource_v2(camera["name"], camera["mac"], camera)
					logger.info("Updated device " + str(camera))
					cameraDbId = id
				else:
					cameraDbId = self.dbCamActions.addVideoSource(camera["name"], camera)
					logger.info("Created new device " + str(camera) + " " + str(cameraDbId))
				self.frameObjConstructor.updateDeviceId(camera["cameraUID"] , cameraDbId)

		pass

	def stop(self):
		self.stop_event()
		self.frameObjConstructor().stop()
		tornado.ioloop.IOLoop.current().stop()
	
	def serverListen(self, port = 9090):
		logger.info("listening for video request connections on port: " + str(port))
		#ToDo: bad practice, merge the tornado video logic with the socket server maybe?
		asyncio.set_event_loop(asyncio.new_event_loop())
		self.server = tornado.httpserver.HTTPServer(self.app)
		self.server.listen(port)
		tornado.ioloop.IOLoop.current().start()
	
	def _make_app(self, frameObjConstructor):
		logger.info("video handler bind server route")
		# add handlers
		return tornado.web.Application([(r'/video_feed', videoFeedHandler, {'frameConstObj': frameObjConstructor})],)
