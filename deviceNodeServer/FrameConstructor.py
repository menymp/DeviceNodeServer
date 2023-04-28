#test cameras
#https://stackoverflow.com/questions/49978705/access-ip-camera-in-python-opencv
# import the opencv library
import cv2
import numpy as np

from Esp32VideoService import Esp32VideoService
from LocalVideoService import LocalVideoService

#init status codes
STATUS_OK = 0
STATUS_ERR = 1
#camera types
ESP32CAM = 1
LOCALCAM = 2

class FrameConstructor():
	def __init__():
		self.deviceDict = {}
		pass
	'''
	argsObj={
		"type":classtype, #esp32 local etc...
		"cameraId":"", #depending on the type, if the type is local
		"host":"",#if the camera is esp32
		"port":"",#if the camera is esp32
		"height":600,
		"width":800,
		"id":111133 #unique identifier for indexing
	}
	'''
	def initNewCamera(self, argsObj):
		result={
			"status":STATUS_OK,
			"msg":""
		}
		try:
			if argsObj["type"] == ESP32CAM:
				camObj = Esp32VideoService(argsObj)
				camObj.start()
				self.deviceDict[argsObj["id"]] = camObj
			elif argsObj["type"] == LOCALCAM:
				camObj = LocalVideoService(argsObj)
				camObj.start()
				self.deviceDict[argsObj["id"]] = camObj
			else
				raise Exception("Camera type not supported")
		except Exception as e:
			camObj.stop()
			result["status"] = STATUS_ERR
			result["msg"] = e
		return result
	
	'''
	argsObj={
		"height":600,
		"width":600,
		"idsList":[1,2,3], #expected ids to be concatenated
		"rowLen":2 #how many images stack in the horizontal
	}
	'''
	#ToDo: stack images there per row
	def buildFrame(self, argsObj):
		toggleFlag = 0
		frame = None
		for id in argsObj.idList:
			if toggleFlag < 
			
		return frame
	
	def getImage(self, id):
		return self.deviceDict[id].getImage()
	
	def stopAllCameras(self):
		for key, value in self.deviceDict.items:
			value.stop