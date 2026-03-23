#test cameras
#https://stackoverflow.com/questions/49978705/access-ip-camera-in-python-opencv
# import the opencv library
import cv2
import numpy as np
from os.path import dirname, realpath, sep, pardir
import asyncio
import logging
import logging
import threading
import json
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
LISTEN_HOST = "0.0.0.0"

class FrameServerConstructor:
    def __init__(self, args, frameObjConstructor=None):
        self._lock = threading.Lock()
        self.deviceDict = {}
        self.dbHost = args[0]
        self.dbName = args[1]
        self.dbUser = args[2]
        self.dbPass = args[3]
        self.stop_event = None
        self.dbCamActions = None
        logger.info("FrameServerConstructor created (sync init): %s", args)

    async def init(self):
        self.dbCamActions = dbVideoActionsAsync()
        await self.dbCamActions.initConnector(self.dbUser, self.dbPass, self.dbHost, self.dbName)
        return self

    async def update_video_sources(self, stop_event: asyncio.Event, interval: float = 2.0):
        """
        Periodic async task: snapshot cameras under lock, then perform DB work without holding the lock.
        If dbCamActions methods are synchronous, run them in a thread via asyncio.to_thread.
        """
        logger.info("update_video_sources started, interval=%s", interval)
        self.stop_event = stop_event
        try:
            while not stop_event.is_set():
                try:
                    logger.debug("updating cameras")
                    # 1) take a short, thread-safe snapshot of cameras
                    with self._lock:
                        # copy values to a list so we can iterate without holding the lock
                        available_cameras = list(self.deviceDict.values())
                        logger.debug(available_cameras)

                    # 2) iterate snapshot and do DB work (no locks held)
                    for camera in available_cameras:
                        camera_encoded = json.dumps(camera)
                        # defensive checks
                        name = camera.get("name")
                        mac = camera.get("mac")
                        cameraUID = camera.get("cameraUID")
                        logger.debug("updating UID" + str(cameraUID))

                        if not name or not mac or not cameraUID:
                            logger.warning("Skipping camera with incomplete metadata: %s", camera)
                            continue

                        # If dbCamActions methods are async (aiomysql), call them directly.
                        # If they are synchronous, wrap them with asyncio.to_thread to avoid blocking the loop.
                        try:
                            # Example: try calling as async; if it raises TypeError or AttributeError,
                            # fall back to running in a thread. This keeps code robust.
                            if asyncio.iscoroutinefunction(self.dbCamActions.videoSourceExists_v2):
                                exists, db_id = await self.dbCamActions.videoSourceExists_v2(name, mac)
                                logger.debug("exists? " + str(cameraUID))
                            else:
                                # run blocking DB call in a thread
                                exists, db_id = await asyncio.to_thread(self.dbCamActions.videoSourceExists_v2, name, mac)
                        except Exception:
                            logger.exception("videoSourceExists_v2 failed for %s", camera)
                            continue

                        if exists:
                            logger.debug("exists, updating" + str(cameraUID))
                            try:
                                if asyncio.iscoroutinefunction(self.dbCamActions.updateVideoSource_v2):
                                    await self.dbCamActions.updateVideoSource_v2(name, mac, camera_encoded)
                                else:
                                    await asyncio.to_thread(self.dbCamActions.updateVideoSource_v2, name, mac, camera_encoded)
                                logger.debug("Updated device %s", cameraUID)
                            except Exception:
                                logger.exception("updateVideoSource_v2 failed for %s", camera)
                        else:
                            logger.info("creating" + str(cameraUID))
                            try:
                                if asyncio.iscoroutinefunction(self.dbCamActions.addVideoSource):
                                    db_id = await self.dbCamActions.addVideoSource(name, camera_encoded)
                                else:
                                    db_id = await asyncio.to_thread(self.dbCamActions.addVideoSource, name, camera_encoded)
                                logger.info("Created new device %s id=%s", cameraUID, db_id)
                            except Exception:
                                logger.exception("addVideoSource failed for %s", camera)
                                db_id = None

                        # 3) update local mapping under lock (short critical section)
                        if cameraUID:
                            with self._lock:
                                entry = self.deviceDict.get(cameraUID)
                                if entry is not None:
                                    entry["dbId"] = db_id
                                else:
                                    logger.warning("updateDeviceId: cameraUID not found %s", cameraUID)
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
        with self._lock:
            return self.deviceDict

    def updateDeviceId(self, deviceUID, dbId):
        if not deviceUID:
            return
        with self._lock:
            camDevice = self.deviceDict[deviceUID]
            if camDevice:
                self.deviceDict[deviceUID]["dbId"] = dbId

    def processCameraHeader(self, type, name, mac, client_ip):
        cameraUID = mac + name
        with self._lock:
            if cameraUID not in self.deviceDict:
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
        logger.debug("frame constructor found devices: " + str(devIdArr))
        return devIdArr
	
    def getDeviceFromDbId(self, dbId):
        for deviceD in self.deviceDict:
            if deviceD["dbId"] == dbId:
                logger.debug("frame constructor found device: " + str(dbId))
                return deviceD
        logger.info("Device not found: " + str(dbId))
        return None

	#ToDo: deep test of every case of failure
	#create the no image from cam driver
    def buildFrame(self, sources, argsObj):
        logger.debug("frame constructor building frame with " + str(argsObj))
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
        if img is None:
            return None
        ret, jpeg = cv2.imencode('.jpg', img)
        return jpeg.tobytes() if ret else None
	
    def stop(self):
        # if stop_event is an asyncio.Event, set it accordingly
        if isinstance(self.stop_event, asyncio.Event):
            self.stop_event.set()
        else:
            try:
                self.stop_event.set()
            except Exception:
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