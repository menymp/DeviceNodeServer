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