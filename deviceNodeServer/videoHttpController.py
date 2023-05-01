import time

import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.process
import tornado.template
import gen
import os

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
		argsObj={"height":600,"width":600,"idList":[1,2,3],"rowLen":2,"idText":True}
		img = self.frameConstObj.getJpg(argsObj)
		
		
		self.write(my_boundary)
		self.write("Content-type: image/jpeg\r\n")
		self.write("Content-length: %s\r\n\r\n" % len(img))
		self.write(img)
		
		self.flush()


class videoHandler():
	def __init__(self):
		app = self._make_app(frameObjConstructor)
		self.server = tornado.httpserver.HTTPServer(app)
		pass
	
	def _initVideoSources(self):
		#ToDo:  this list should be loaded from database
		self.frameObjConstructor = FrameConstructor()
		#connArgs should be fetch from database
		#frameObjConstructor.initNewCamera(connArgs3)
		pass
	
	def serverListen(self):
		self.server.listen(9090)
		self.tornado.ioloop.IOLoop.current().start()
	
	def _make_app(frameObjConstructor):
		# add handlers
		return tornado.web.Application([(r'/video_feed', videoFeedHandler, {'frameConstObj': frameObjConstructor})],)
