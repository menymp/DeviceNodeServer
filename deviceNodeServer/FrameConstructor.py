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
	def __init__(self):
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
			else:
				raise Exception("Camera type not supported")
		except Exception as e:
			camObj.stop()
			result["status"] = STATUS_ERR
			result["msg"] = e
		return result
	
	def getDeviceIds(self):
		devIdArr = []
		for deviceD in self.deviceDict:
			devIdArr.append(deviceD)
		return devIdArr
	
	'''
	argsObj={
		"height":600,
		"width":600,
		"idsList":[1,2,3], #expected ids to be concatenated
		"rowLen":2, #how many images stack in the horizontal
		"idText":True #enable video id for source
	}
	'''
	#ToDo: deep test of every case of failure
	#create the no image from cam driver
	def buildFrame(self, argsObj):
		toggleFlag = 0
		frameRow = None
		frame = None
		for id in argsObj["idList"]:
			flag, img = self.deviceDict[id].getImage()
			img = cv2.resize(img, (argsObj["height"], argsObj["width"]))
			
			if argsObj["idText"] == True:
				img = cv2.putText(img, "Source " + str(id), (10,argsObj["height"] - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
			
			if frameRow is None:
				frameRow = img
				toggleFlag = toggleFlag + 1
				continue
			elif toggleFlag < argsObj["rowLen"]:
				frameRow = np.hstack((frameRow,img))
				toggleFlag = toggleFlag + 1
				continue
			elif toggleFlag == argsObj["rowLen"] and frame is None:
				frame = np.copy(frameRow)
				frameRow = img
				toggleFlag =  1
				continue
			elif toggleFlag == argsObj["rowLen"] and frame is not None:
				frame = np.vstack((frame,frameRow))
				frameRow = None
				frameRow = img
				toggleFlag = 1
				continue
		
		if frame is not None and frameRow is not None and toggleFlag == argsObj["rowLen"]:
			frame = np.vstack((frame,frameRow))
		
		if toggleFlag > 0 and toggleFlag < argsObj["rowLen"] and frameRow is not None:
			h = img.shape[0]
			w = img.shape[1]
			paddWidth = argsObj["rowLen"] - toggleFlag
			paddImg = np.zeros((h,w*paddWidth,3), dtype=np.uint8)
			frameRow = np.hstack((frameRow,paddImg))
			
			if frame is None:
				frame = frameRow
			else:
				frame = np.vstack((frame,frameRow))
			
		if frame is None:
			frame = frameRow
		return frame
	
	def getJpg(self, argsObj):
		img = self.buildFrame(argsObj)
		ret, jpeg = cv2.imencode('.jpg', img)
		return jpeg.tobytes()
	
	def getImage(self, id):
		return self.deviceDict[id].getImage()
	
	def stopAllCameras(self):
		for key, value in self.deviceDict.items:
			value.stop
