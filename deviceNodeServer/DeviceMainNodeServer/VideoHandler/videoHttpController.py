import time
import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.process
import tornado.template
import gen
import os
from threading import Timer
import json
import asyncio
import sys

from os.path import dirname, realpath, sep, pardir
# Get current main.py directory
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DBUtils")

from dbActions import dbVideoActions
from FrameConstructor import *

class videoFeedHandler(tornado.web.RequestHandler):
	def initialize(self, frameConstObj):
		self.frameConstObj = frameConstObj
	
	@tornado.gen.coroutine
	def get(self):
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
		self.dbHost = args[0]
		self.dbName = args[1]
		self.dbUser = args[2]
		self.dbPass = args[3]
		self._initVideoSources()
		self.app = self._make_app(self.frameObjConstructor)
		pass
	
	def _initVideoSources(self):
		self.dbActions = dbVideoActions()
		self.dbActions.initConnector(self.dbUser,self.dbPass,self.dbHost,self.dbName)
		self.videoSources = self.dbActions.getVideoSources()
		
		self.frameObjConstructor = FrameConstructor()
		
		for deviceInfo in self.videoSources:
			connArgs=json.loads(deviceInfo[3])
			connArgs["name"]=deviceInfo[1]
			connArgs["id"]=deviceInfo[0]
			connArgs["idCreator"]=deviceInfo[2]
			self.frameObjConstructor.initNewCamera(connArgs)
			pass
		self.startTimerFetch()
		pass
	
	#ToDo: implement time as a parameter
	def startTimerFetch(self):
		self.timerSec = Timer(7.0, self._timerGetNewVideoSources).start()
		self.stop = False
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
		pass
	
	#ToDo: need to implement a char update method to restart the camera obj when a change
	#		is detected, for now leave this as it is
	def _timerGetNewVideoSources(self):
		if self.stop:
			return
		newVideoSources = self.dbActions.getVideoSources()
		#ToDo: DRY principle
		currentDeviceIds = self.frameObjConstructor.getDeviceIds()
		for deviceInfo in newVideoSources:
			if deviceInfo[0] not in  currentDeviceIds:
				connArgs=deviceInfo[3]
				connArgs["name"]=deviceInfo[1]
				connArgs["id"]=deviceInfo[0]
				connArgs["idCreator"]=deviceInfo[2]
				self.frameObjConstructor.initNewCamera(connArgs)
			pass
		
		self.timerSec = Timer(7.0, self._timerGetNewVideoSources).start()
		pass
	
	#ToDo: use this in the item destructor
	def stopTimerFetch(self):
		self.stop = True
		pass

	def stop(self):
		self.stop = True
		tornado.ioloop.IOLoop.current().stop()
	
	def serverListen(self):
		#ToDo: bad practice, merge the tornado video logic with the socket server maybe?
		asyncio.set_event_loop(asyncio.new_event_loop())
		self.server = tornado.httpserver.HTTPServer(self.app)
		self.server.listen(9090)
		tornado.ioloop.IOLoop.current().start()
	
	def _make_app(self, frameObjConstructor):
		# add handlers
		return tornado.web.Application([(r'/video_feed', videoFeedHandler, {'frameConstObj': frameObjConstructor})],)
