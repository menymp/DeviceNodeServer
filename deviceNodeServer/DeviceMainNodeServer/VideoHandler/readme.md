videoHandler

-provides a service of video seeds for the UI, this server will keep a request for each of the
video seeds. every time a video request is performed, a frame can be placed depending on the command
requeriments.
-multiple frames can be requested in the same operation.



'BaseVideoService' class implements the common functions for the video stream devices.
below are the common methods:
- starts() performs the thread start for the video, this thread will perform calls to the _taskUpdateImage method
- stop() stops the video image update
- _updateImage() performst the image update call
- getImage() returns the current stored frame as well as a flag to determine if there were available frames
- getJpg() performs a getImage call and converts to .jpg for web display

'LocalVideoService' specialized class to implement the funcionalities to retrive a local image from a local camera device asociated with the server device.
below are the common methods
- _taskUpdateImage method task with the procedures for video data from the local camera
- set_resolution method to set the resolution properties for the camera conversion

'Esp32VideoService' specialized class to implement the functionalities to retrive an esp32 image from a esp32 cam module available in the network.
below are the common methods
- _taskUpdateImage method task that request the video from the local camera and converts into a image

'FrameConstructor' this class contains utilities for the request frame constructor that helps the websocket request to build specialized frames of images for the requested video sources.
below are the members of the class
-  __init__ inits the class and resets the deviceDict list class
- initNewCamera adds a new camera source object, these are the expected for of the arg request object: 
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
- getDevicesIds obtains a list of the current available devices id.
- buildFrame build a frame with the given request parameters and returns a status flag and a image if available, below an example of the object structure
	'''
	argsObj={
		"height":600,
		"width":600,
		"idsList":[1,2,3], #expected ids to be concatenated
		"rowLen":2, #how many images stack in the horizontal
		"idText":True #enable video id for source
	}
	'''
- getJpg obtains a jpg form of the buildFrame callback, check buildFrame for the args structure.
- getImage obtains an image from the deviceDict based on an available id
- stopAllCameras stops the update execution for all the available camera sources

'videoFeedHandler' this class handles the request of a jpg image over http for a web based application.
below are the defined actions
- get starts with a request of a .jpg frame
a request should be in the following form
'''
argsObj={"height":600,"width":600,"idList":[1,2,3],"rowLen":2,"idText":True}
'''

'videoHandler' this is the main server class for the video service that implements the web tornado server, below are the members of the execution process
- __init__ inits the credentials for the server, as well as the available video sources and the web tornado app.
- _initVideoSources inits the available registered video sources in the frame, once it finishes, a new process will start each 7 seconds to update the available devices if not already init.
- startTimerFetch starts a new timer each 7 seconds that calls the _timerGetNewVideoSources callback for the video sources update.
- execCommand runs command to request video frames
- _timerGetNewVideoSources this will call getVideoSources db action to retrive available source video devices from the db register
- stopTimerFetch stops the current device fetch timer
- stop stops the server execution
- serverListen starts the http callback for the server listen
- _make_app handles of web request