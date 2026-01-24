 #!/usr/bin/python
#coding:utf-8
import os.path

import tornado.httpserver
import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpclient
import tornado.websocket

import json

import sys
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")

from loggerUtils import get_logger
logger = get_logger(__name__)

class wSocketServerManager():
    def init(self, socketPort):
        self.socketPort = socketPort
        logger.info("new web socket server instance in port: " + str(socketPort))
        pass

    def serverListen(self, on_MessageCmd):
        logger.info("socket handler server listening")
        self.app = tornado.web.Application(handlers=[(r"/workHandler", SocketHandler)],debug = True, template_path = os.path.join(os.path.dirname(__file__), "templates"),static_path = os.path.join(os.path.dirname(__file__), "static"), on_messageHandler = on_MessageCmd)
        #app.init(on_MessageCmd) #colocar el metodo de ejecutar comando
        self.app.listen(self.socketPort)
        tornado.ioloop.IOLoop.instance().start()
        pass

    def stop(self):
        tornado.ioloop.IOLoop.current().stop()

class SocketHandler(tornado.websocket.WebSocketHandler):
    """docstring for SocketHandler"""
    clients = set()
    # def check_origin(self, origin):
        # allowed = ["https://site1.tld", "https://site2.tld"]
        # if origin in allowed:
            # print("allowed", origin)
            # return 1
    def check_origin(self, origin):
        return True

    def initialize(self):
        self.on_messageHandler = self.application.settings.get('on_messageHandler')
    
    @staticmethod
    def send_to_all(message):
        logger.info("broadcasting message: " + str(message))
        for c in SocketHandler.clients:
            c.write_message(json.dumps(message))

    def open(self):
        logger.info("new open channel ")
        #self.write_message(json.dumps({'type': 'sys','message': 'Welcome to WebSocket',}))
        SocketHandler.clients.add(self)

    #def init(self, on_messageS):
    #    self.on_messageHandler = on_messageS
    #    pass

    def on_close(self):
        logger.info("web socket handler closing")
        pass
    #process an array with commands to execute
    def on_message(self, message):
        logger.info("web socket handler new message arrived: " + str(message))
        #print(message)
        #json_message = json.dumps(message)
        #
        #ToDo: What would happen if many messages arrives at the same time
        #      should it have a queue for message handling?
        #
        try:
            result = self.on_messageHandler(message)
            self.write_message(result)
            logger.info("web socket handler result: " + str(result))
        except:
            logger.error('socket message processing error')
        pass

##MAIN
#if __name__ == '__main__':
#    app = tornado.web.Application(handlers=[(r"/workHandler", SocketHandler)],debug = True, template_path = os.path.join(os.path.dirname(__file__), "templates"),static_path = os.path.join(os.path.dirname(__file__), "static"))
#    app.listen(8112)
#    tornado.ioloop.IOLoop.instance().start()