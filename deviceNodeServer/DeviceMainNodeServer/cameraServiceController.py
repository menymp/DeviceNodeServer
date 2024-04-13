#by https://github.com/Jatin1o1/Python-Javascript-Websocket-Video-Streaming-/blob/main/Video_server_websocket.py
#!/usr/bin/env python

# WS server that sends camera streams to a web server using opencv

#better approach using tornado? 
#https://quantum-inc.medium.com/remote-video-streaming-with-face-detection-d52ce2d71419
import asyncio
import websockets
import cv2

from Esp32VideoService import Esp32VideoService

import time

import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.process
import tornado.template

class StreamHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        ioloop = tornado.ioloop.IOLoop.current()
		#ToDo: camera type should be part of a parameter, there can be defined the proper driver
		#ToDo: wire connArgs as the container for the parameters, for example, for esp32 cam the ip and port
		cam = Esp32VideoService(connArgs)
		cam.start()
		
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
        self.set_header( 'Pragma', 'no-cache')
        self.set_header( 'Content-Type', 'multipart/x-mixed-replace;boundary=--jpgboundary')
        self.set_header('Connection', 'close')
		
        self.served_image_timestamp = time.time()
        my_boundary = "--jpgboundary"
        while True:
            # Generating images for mjpeg stream and wraps them into http resp
            #if self.get_argument('fd') == "true":
            #    img = cam.get_frame(True)
            #else:
            #    img = cam.get_frame(False)
			img = cam.getImage()
			
            interval = 0.1
            if self.served_image_timestamp + interval < time.time():
                self.write(my_boundary)
                self.write("Content-type: image/jpeg\r\n")
                self.write("Content-length: %s\r\n\r\n" % len(img))
                self.write(img)
                self.served_image_timestamp = time.time()
                yield tornado.gen.Task(self.flush)
            else:
                yield tornado.gen.Task(ioloop.add_timeout, ioloop.time() + interval)

class HtmlPageHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, file_name='index.html'):
        # Check if page exists
        index_page = os.path.join(html_page_path, file_name)
        if os.path.exists(index_page):
            # Render it
            self.render('www/' + file_name)
        else:
            # Page not found, generate template
            err_tmpl = tornado.template.Template("<html> Err 404, Page {{ name }} not found</html>")
            err_html = err_tmpl.generate(name=file_name)
            # Send response
            self.finish(err_html)

#init tornado app
def make_app():
    # add handlers
    return tornado.web.Application([
        (r'/', HtmlPageHandler),
        (r'/video_feed', StreamHandler),
        (r'/setparams', SetParamsHandler),
        (r'/(?P<file_name>[^\/]+htm[l]?)+', HtmlPageHandler),
        (r'/(?:image)/(.*)', tornado.web.StaticFileHandler, {'path': './image'}),
        (r'/(?:css)/(.*)', tornado.web.StaticFileHandler, {'path': './css'}),
        (r'/(?:js)/(.*)', tornado.web.StaticFileHandler, {'path': './js'})
        ],
    )

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