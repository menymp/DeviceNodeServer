#!/usr/bin/env python
from io import BytesIO
import cv2
import numpy as np
from BaseVideoService import BaseVideoService

import sys
from os.path import dirname, realpath, sep, pardir
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")

from loggerUtils import get_logger
logger = get_logger(__name__)

class LocalVideoService(BaseVideoService):
	def _taskUpdateImage(self, connectionArgs):
		logger.info("local video service start with " + str(connectionArgs))
		# select first video device in system
		self.cam = cv2.VideoCapture(connectionArgs["cameraId"])
		# set camera resolution
		self.w = connectionArgs["width"]
		self.h = connectionArgs["height"]
		# set crop factor
		self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.h)
		self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, self.w)
		
		while not self.stopEvent.is_set():
			success, image = self.cam.read()
			if success:
			# scale image
				image = cv2.resize(image, (self.w, self.h))
				#image = np.zeros((self.h, self.w, 3), np.uint8)
				#cv2.putText(image, 'No camera', (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1)
			# encoding picture to jpeg
			#ret, jpeg = cv2.imencode('.jpg', image)
			self._updateImage(image)
		pass
	
	#ToDo: h and w are shared by the thread, so a threadsafe approach should be 
	#      implemented in the future
	def set_resolution(self, new_w, new_h):
		logger.info("local video service setting frame resolution to " + str((new_w, new_h)))
		if isinstance(new_h, int) and isinstance(new_w, int):
			# check if args are int and correct
			if (new_w <= 800) and (new_h <= 600) and \
				(new_w > 0) and (new_h > 0):
				self.h = new_h
				self.w = new_w
			else:
				# bad params
				raise Exception('Bad resolution')
		else:
			# bad params
			raise Exception('Not int value')
	'''
    def __init__(self, connectionArgs):
        # select first video device in system
        self.cam = cv2.VideoCapture(connectionArgs["cameraId"])
        # set camera resolution
        self.w = connectionArgs["width"]
        self.h = connectionArgs["height"]
        # set crop factor
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.h)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, self.w)
	
    def set_resolution(self, new_w, new_h):
        if isinstance(new_h, int) and isinstance(new_w, int):
            # check if args are int and correct
            if (new_w <= 800) and (new_h <= 600) and \
               (new_w > 0) and (new_h > 0):
                self.h = new_h
                self.w = new_w
            else:
                # bad params
                raise Exception('Bad resolution')
        else:
            # bad params
            raise Exception('Not int value')

    def get_frame(self, fdenable):
        success, image = self.cam.read()
        if success:
            # scale image
            image = cv2.resize(image, (self.w, self.h))
            image = np.zeros((self.h, self.w, 3), np.uint8)
            cv2.putText(image, 'No camera', (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1)
        # encoding picture to jpeg
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()
	'''
'''
simple test code
'''
'''
connArgs = {
	"cameraId":0,
	"height":600,
	"width":800
}

camObj = LocalVideoService(connArgs)
camObj.start()
cnt = 0

while cnt < 200:
	state, img = camObj.getImage()
	if state:
		cnt = cnt + 1
		cv2.imshow("img", img)
		cv2.waitKey(10)
camObj.stop()
print("bye")
'''