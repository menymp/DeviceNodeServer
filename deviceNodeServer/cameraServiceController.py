#by https://github.com/Jatin1o1/Python-Javascript-Websocket-Video-Streaming-/blob/main/Video_server_websocket.py
#!/usr/bin/env python

# WS server that sends camera streams to a web server using opencv

#better approach using tornado? 
#https://quantum-inc.medium.com/remote-video-streaming-with-face-detection-d52ce2d71419
import asyncio
import websockets
import cv2
#ToDo: at this level different types of cameras are expected to be handled
from Esp32VideoService import Esp32VideoService
    
async def wsImageHandler(websocket, path):
	

    while True:

        
        try:
            while(vid.isOpened()):
                
                img, frame = vid.read()
                
                frame = cv2.resize(frame, (640, 480))
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 65]
                man = cv2.imencode('.jpg', frame, encode_param)[1]
                #sender(man)
                await websocket.send(man.tobytes())
                
        except :

            
            pass
                
start_server = websockets.serve(time, "127.0.0.1", 9997)    
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()