from threading import Thread
from threading import Lock
from threading import Event
import socket                   # Import socket module
from io import BytesIO
import cv2
import numpy as np

class BaseVideoService():
	def __init__(self, connectionArgs):
		self.connectionArgs = connectionArgs
		self.image = np.zeros((600,600,3))
		pass
	
	def start(self):
		self.stopEvent = Event()
		self.stopEvent.clear()
		self.writeEvent = Event()
		self.writeEvent.set()
		self.taskUpdateImage = Thread(target=self._taskUpdateImage, args = (self.connectionArgs, ))
		self.taskUpdateImage.start()
		pass
	
	def stop(self):
		if self.stopEvent:
			self.stopEvent.set()
		pass
	
	# to be implemented by the child class
	#def _taskUpdateImage(self, host, port, closeEvent):
	#	pass
	
	def _updateImage(self, image):
		self.writeEvent.clear()
		self.image = image
		self.writeEvent.set()
	
	def getImage(self):
		if self.image is None:
			return False, None
		self.writeEvent.wait()
		imageTmp = self.image
		return True, imageTmp
	
	def getJpg(self):
		rs, img = self.getImage()
		if not rs:
			return False, None
		ret, jpeg = cv2.imencode('.jpg', img)
		return jpeg.tobytes()