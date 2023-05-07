'''
https://github.com/wildfios/Tornado-mjpeg-streamer-python

https://stackoverflow.com/questions/56964487/tornado-6-0-3-from-4-2-module-tornado-web-has-no-attribute-asynchronous

https://docs.huihoo.com/tornado/4.2/gen.html#tornado.gen.Task
https://www.tornadoweb.org/en/stable/gen.html#module-tornado.gen
https://www.tornadoweb.org/en/stable/concurrent.html#tornado.concurrent.Future

https://stackoverflow.com/questions/57103331/how-to-replace-yield-gen-taskfn-argument-with-an-equivalent-asyncio-express
If you're stuck with something that takes a callback and you can't change it, this sequence is almost equivalent to response = yield gen.Task(fn, request):

future = tornado.concurrent.Future()
fn(request, callback=future.set_result)
response = yield future

https://github.com/wildfios/Tornado-mjpeg-streamer-python/issues/7
'''
import time

import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.process
import tornado.template
import video
import gen
import os
import sys
sys.path.append("..")

from FrameConstructor import *
#from Esp32VideoService import Esp32VideoService
#from LocalVideoService import LocalVideoService

#cam = None
html_page_path = dir_path = os.path.dirname(os.path.realpath(__file__)) + '/www/'


class HtmlPageHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
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


class SetParamsHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def post(self):
        # print self.request.body
        # get args from POST request
        width = int(self.get_argument('width'))
        height = int(self.get_argument('height'))
        # try to change resolution
        try:
            #cam.set_resolution(width, height)
            self.write({'resp': 'ok'})
        except:
            self.write({'resp': 'bad'})
            self.flush()
            self.finish()


class StreamHandler(tornado.web.RequestHandler):
    def initialize(self, cam):
        self.cam = cam
	
    @tornado.gen.coroutine
    def get(self):
        ioloop = tornado.ioloop.IOLoop.current()

        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
        self.set_header( 'Pragma', 'no-cache')
        self.set_header( 'Content-Type', 'multipart/x-mixed-replace;boundary=--jpgboundary')
        self.set_header('Connection', 'close')

        self.served_image_timestamp = time.time()
        my_boundary = "--jpgboundary"
        
        '''
        argsObj={
	        "height":600,
	        "width":600,
	        "idList":[1], #expected ids to be concatenated
	        "rowLen":2, #how many images stack in the horizontal
			"idText":True
        }
        '''
		
        while True:
            # Generating images for mjpeg stream and wraps them into http resp
            argsObj = json.loads(self.get_argument('vidArgs'))
            #img = cam.get_frame(True)
            img = self.cam.getJpg(argsObj)
            #img = cam.get_frame(False)
            #img = self.cam.getJpg(argsObj)
            interval = 0.1
            if self.served_image_timestamp + interval < time.time():
                self.write(my_boundary)
                self.write("Content-type: image/jpeg\r\n")
                self.write("Content-length: %s\r\n\r\n" % len(img))
                #print(img)
                #print(type(img))
                self.write(img)
                self.served_image_timestamp = time.time()
                #yield tornado.gen.Task(self.flush)
				#self.flush()
                yield self.flush()
            else:
                #yield tornado.gen.Task(ioloop.add_timeout, ioloop.time() + interval)
                def _callbackF():
                    pass
                ioloop.add_timeout(ioloop.time() + interval, _callbackF)

class videoFeedHandler(tornado.web.RequestHandler):
	def initialize(self, frameConstObj):
		self.frameConstObj = frameConstObj
	
	@tornado.gen.coroutine
	def get(self):
		self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
		self.set_header( 'Pragma', 'no-cache')
		self.set_header( 'Content-Type', 'multipart/x-mixed-replace;boundary=--jpgboundary')
		self.set_header('Connection', 'close')
		
		my_boundary = "--jpgboundary"
		
		argsObj={"height":600,"width":600,"idList":[1],"rowLen":2,"idText":True}
		img = self.frameConstObj.getJpg(argsObj)
		
		
		self.write(my_boundary)
		self.write("Content-type: image/jpeg\r\n")
		self.write("Content-length: %s\r\n\r\n" % len(img))
		self.write(img)
		
		self.flush()

#https://stackoverflow.com/questions/55995128/how-can-i-constantly-update-an-image
def make_app(frameObjConstructor):
    # add handlers
    return tornado.web.Application([
        (r'/', HtmlPageHandler),
        #(r'/video_feed', StreamHandler, {'cam': frameObjConstructor}),
		(r'/video_feed', videoFeedHandler, {'frameConstObj': frameObjConstructor}),
		#(r'/video_feed2', StreamHandler, {'cam': cam}),
        (r'/setparams', SetParamsHandler),
        (r'/(?P<file_name>[^\/]+htm[l]?)+', HtmlPageHandler),
        (r'/(?:image)/(.*)', tornado.web.StaticFileHandler, {'path': './image'}),
        (r'/(?:css)/(.*)', tornado.web.StaticFileHandler, {'path': './css'}),
        (r'/(?:js)/(.*)', tornado.web.StaticFileHandler, {'path': './js'})
        ],
    )


if __name__ == "__main__":
    #creates camera
    #cam = video.UsbCamera()
	# bind server on 8080 port
    app = make_app(frameObjConstructor)
    server = tornado.httpserver.HTTPServer(app)
    server.listen(9090)
    #app.listen(9090)
    tornado.ioloop.IOLoop.current().start()
