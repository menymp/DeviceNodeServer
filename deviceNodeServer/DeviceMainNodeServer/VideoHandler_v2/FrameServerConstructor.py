#test cameras
#https://stackoverflow.com/questions/49978705/access-ip-camera-in-python-opencv
# import the opencv library
import cv2
import numpy as np
from os.path import dirname, realpath, sep, pardir
from threading import Thread, Event
import time
import asyncio
import aiomysql
import logging
# Get current main.py directory

import sys
from os.path import dirname, realpath, sep, pardir
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")
sys.path.append(dirname(realpath(__file__)) + sep + pardir)
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DButils")

from loggerUtils import get_logger
logger = get_logger(__name__)

from dbActions import dbVideoActionsAsync
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
'''
		while self.stop_event.is_set() == False:
			availableCameras = self.get_cameras_info()
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
			time.sleep(2)
		pass
'''

import asyncio
import logging
import os
import signal

from async_db import AsyncDB            # your aiomysql wrapper
from db_actions import dbVideoActionsAsync  # your async DB actions wrapper
from server import start_tcp_server, start_http_server  # your server starters

logger = logging.getLogger(__name__)
LISTEN_HOST = "0.0.0.0"

class FrameServerConstructor:
    def __init__(self, args, frameObjConstructor = None):
        # synchronous init only
        self.deviceDict = {}
        self.dbHost = args[0]
        self.dbName = args[1]
        self.dbUser = args[2]
        self.dbPass = args[3]
        self.stop_event = None
        self.dbCamActions = None
        logger.info("FrameServerConstructor created (sync init): %s", args)

    async def init(self):
        """
        Async factory: constructs instance and performs async initialization.
        """
        # initialize async DB actions wrapper
        self.dbCamActions = dbVideoActionsAsync()
        await self.dbCamActions.initConnector(self.dbUser, self.dbPass, self.dbHost, self.dbName)
        return self

    async def update_video_sources(self, stop_event: asyncio.Event, interval: float = 2.0):
        """
        Periodic async task: every `interval` seconds, sync camera info with DB.
        """
        logger.info("update_video_sources started, interval=%s", interval)
        self.stop_event = stop_event
        try:
            while not stop_event.is_set():
                try:
                    available_cameras = await self.get_cameras_info()
                    for camera in available_cameras:
                        try:
                            exists, db_id = await self.dbCamActions.videoSourceExists_v2(
                                camera["name"], camera["mac"]
                            )
                        except Exception:
                            logger.exception("videoSourceExists_v2 failed for %s", camera)
                            continue

                        if exists:
                            try:
                                await self.dbCamActions.updateVideoSource_v2(camera["name"], camera["mac"], camera)
                                logger.info("Updated device %s", camera)
                            except Exception:
                                logger.exception("updateVideoSource_v2 failed for %s", camera)
                        else:
                            try:
                                db_id = await self.dbCamActions.addVideoSource(camera["name"], camera)
                                logger.info("Created new device %s id=%s", camera, db_id)
                            except Exception:
                                logger.exception("addVideoSource failed for %s", camera)
                                db_id = None

                        
                        self.updateDeviceId(camera["cameraUID"], db_id)
                except Exception:
                    logger.exception("Error in update_video_sources loop")

                # wait for interval or until stop_event is set
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=interval)
                except asyncio.TimeoutError:
                    # timeout expired -> loop again
                    pass
        except asyncio.CancelledError:
            logger.info("update_video_sources cancelled")
            raise
        finally:
            logger.info("update_video_sources stopped")

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
            newCam = {
				"type": type,
				"height":600, # In the future make this reconfigurable would be a good idea
				"width":800,  # In the future make this reconfigurable would be a good idea
				"mac": mac,
				"name": name,
				"ip": client_ip,
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

	#ToDo: deep test of every case of failure
	#create the no image from cam driver
    def buildFrame(self, sources, argsObj):
        logger.info("frame constructor building frame with " + str(argsObj))
        toggleFlag = 0
        frameRow = None
        frame = None
        for id in argsObj["idList"]:
            device = self.getDeviceFromDbId(id)
            if not device:
                continue

            ts, hdr, img = sources[device["cameraUID"]]
            nparr = np.frombuffer(img, dtype=np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)   # BGR image or None on failure
            if frame is None:
                raise RuntimeError("jpeg decode failed")
			
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
	
    def getJpg(self, sources, argsObj):
        img = self.buildFrame(sources, argsObj)
        ret, jpeg = cv2.imencode('.jpg', img)
        return jpeg.tobytes()
	
    def stop(self):
        self.stop_event.set()