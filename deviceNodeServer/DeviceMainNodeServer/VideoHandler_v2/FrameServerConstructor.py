#test cameras
#https://stackoverflow.com/questions/49978705/access-ip-camera-in-python-opencv
# import the opencv library
import cv2
import numpy as np
import socket                   # Import socket module
from io import BytesIO

from BaseVideoHandler import BaseVideoHandler

import sys
from os.path import dirname, realpath, sep, pardir
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")

from loggerUtils import get_logger
logger = get_logger(__name__)

#init status codes
STATUS_OK = 0
STATUS_ERR = 1
#camera types
ESP32CAM = 1
LOCALCAM = 2


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

class FrameServerConstructor():
	def __init__(self):
		logger.info("frame constructor instance started ")
		self.deviceDict = {}

		#add threading mix in server TODO meny
		#
		# HERE INIT SERVER AND DO THE NAME MAC PROTOCOL

		# NAME#CAM_TYPE#MAC#JPG_DATA_FRAME....    call processCameraHeader then store the video in a secure place

		pass
	'''
	camera client that connected

	'''
	def decode_image(self, client, camera):
		#s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		#s.connect((connectionArgs["host"], connectionArgs["port"]))
		#s.send(b"k") #comando de captura
		f = BytesIO()
		while True:
			data = client.recv(1024)
			if not data:
				f.seek(0)
				break
			f.write(data)
			
			client.close() #indicate client that data was received
			img = cv2.imdecode(np.frombuffer(f.read(), np.uint8), 1)
			camera.updateImage(img)

	def get_cameras_info(self):
		return self.deviceDict

	def updateDeviceId(self, deviceUID, dbId):
		camDevice = self.deviceDict[deviceUID]
		if camDevice:
			self.deviceDict[deviceUID]["dbId"] = dbId

	def processCameraHeader(self, type, name, mac, client_ip):
		cameraUID = mac + name

		if self.deviceDict[cameraUID] is None:
			# ADD CAMERA TO DATA
			logger.info("Adding new camera" + cameraUID)
			resolution = { 
				"height":600, 
				"width":800 
			}
			newCam = {
				"type": type,
				"height":600, # In the future make this reconfigurable would be a good idea
				"width":800,  # In the future make this reconfigurable would be a good idea
				"mac": mac,
				"name": name,
				"ip": client_ip,
				"videoHandler": BaseVideoHandler(resolution),
				"dbId": -1,
				"cameraUID": cameraUID
			}
			self.deviceDict[cameraUID] = newCam
		else:
			self.deviceDict[cameraUID]["type"] = type
			self.deviceDict[cameraUID]["ip"] = client_ip
		return self.deviceDict[cameraUID]

		
	
	def getDeviceIds(self):
		devIdArr = []
		for deviceD in self.deviceDict:
			devIdArr.append(deviceD["dbId"])
		logger.info("frame constructor found devices: " + str(devIdArr))
		return devIdArr
	
	def getDeviceFromDbId(self, dbId):
		for deviceD in self.deviceDict:
			if deviceD["dbId"] == dbId:
				logger.info("frame constructor found device: " + str(dbId))
				return deviceD
		logger.info("Device not found: " + str(dbId))
		return None
	
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
		logger.info("frame constructor building frame with " + str(argsObj))
		toggleFlag = 0
		frameRow = None
		frame = None
		for id in argsObj["idList"]:
			device = self.getDeviceFromDbId(id)
			if not device:
				continue
			flag, img = device["videoHandler"].getImage()
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