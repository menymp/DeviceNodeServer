#!/usr/bin/python
#coding:utf-8
import os.path
from os.path import dirname, realpath, sep, pardir
import urllib.parse
import json
import logging

import tornado.httpserver
import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpclient
import tornado.websocket

import sys
sys.path.append(dirname(realpath(__file__)) + sep + pardir + sep + "DockerUtils")

from loggerUtils import get_logger
logger = get_logger(__name__)

# Read auth service configuration from environment
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://php-node-service:80')
AUTH_VALIDATE_PATH = os.getenv('AUTH_VALIDATE_PATH', '/api/users/')  # endpoint that returns user payload when token valid
AUTH_VALIDATE_FULL = AUTH_SERVICE_URL.rstrip('/') + AUTH_VALIDATE_PATH

class wSocketServerManager():
    def init(self, socketPort):
        self.socketPort = socketPort
        logger.info("new web socket server instance in port: " + str(socketPort))
        pass

    def serverListen(self, on_MessageCmd):
        logger.info("socket handler server listening")
        # pass on_messageHandler via application settings
        self.app = tornado.web.Application(
            handlers=[(r"/workHandler", SocketHandler)],
            debug = True,
            template_path = os.path.join(os.path.dirname(__file__), "templates"),
            static_path = os.path.join(os.path.dirname(__file__), "static"),
            on_messageHandler = on_MessageCmd
        )
        self.app.listen(self.socketPort)
        tornado.ioloop.IOLoop.instance().start()
        pass

    def stop(self):
        tornado.ioloop.IOLoop.current().stop()

class SocketHandler(tornado.websocket.WebSocketHandler):
    """WebSocket handler with Bearer token authentication via PHP auth service"""
    clients = set()

    def check_origin(self, origin):
        # Keep your existing origin policy; returning True allows all origins.
        return True

    def initialize(self):
        self.on_messageHandler = self.application.settings.get('on_messageHandler')
        self.user = None

    @staticmethod
    def send_to_all(message):
        logger.info("broadcasting message: " + str(message))
        for c in list(SocketHandler.clients):
            try:
                c.write_message(json.dumps(message))
            except Exception as e:
                logger.error("error broadcasting to client: " + str(e))

    def open(self):
        """
        Called when a new WebSocket connection is opened.
        Authenticate the client using the token provided in the query string or Authorization header.
        """
        logger.info("new open channel, attempting authentication")
        try:
            token = self._extract_token()
            if not token:
                logger.warning("no token provided, closing connection")
                self.close(code=4001, reason="authentication_required")
                return

            # Validate token synchronously (simple approach)
            user_payload = self._validate_token_with_auth_service(token)
            if not user_payload:
                logger.warning("token validation failed, closing connection")
                self.close(code=4002, reason="invalid_token")
                return

            # Attach user payload to the handler for later use
            self.user = user_payload
            logger.info(f"authenticated websocket user: {self.user}")
            SocketHandler.clients.add(self)
        except Exception as e:
            logger.error("exception during websocket open: " + str(e))
            try:
                self.close(code=1011, reason="server_error")
            except:
                pass

    def on_close(self):
        logger.info("web socket handler closing")
        try:
            if self in SocketHandler.clients:
                SocketHandler.clients.remove(self)
        except Exception:
            pass

    def on_message(self, message):
        logger.info("web socket handler new message arrived: " + str(message))
        # If not authenticated, ignore messages
        if not self.user:
            logger.warning("received message from unauthenticated socket; ignoring")
            try:
                self.write_message(json.dumps({'error': 'unauthenticated'}))
            except:
                pass
            return

        try:
            result = self.on_messageHandler(message)
            # If the handler returns a dict or JSON string, send it back
            if isinstance(result, (dict, list)):
                self.write_message(json.dumps(result))
            else:
                self.write_message(result)
            logger.info("web socket handler result: " + str(result))
        except Exception as e:
            logger.error('socket message processing error: ' + str(e))
            try:
                self.write_message(json.dumps({'error': 'processing_error'}))
            except:
                pass

    # -------------------------
    # Helper methods
    # -------------------------
    def _extract_token(self):
        """
        Extract token from:
         - query param 'token' (preferred)
         - Authorization header 'Bearer <token>'
         - Sec-WebSocket-Protocol header (if you choose to use it)
        """
        # 1) query string
        query = urllib.parse.urlparse(self.request.uri).query
        qs = urllib.parse.parse_qs(query)
        token_list = qs.get('token') or qs.get('access_token')
        if token_list:
            return token_list[0]

        # 2) Authorization header
        auth_header = self.request.headers.get('Authorization') or self.request.headers.get('authorization')
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                return parts[1]

        # 3) Sec-WebSocket-Protocol (optional fallback)
        protocols = self.request.headers.get('Sec-WebSocket-Protocol') or self.request.headers.get('sec-websocket-protocol')
        if protocols:
            # If you used a single protocol value containing token, parse it here.
            # Example: client sets subprotocol to "token,<token>" or just the token.
            # This is optional and depends on client implementation.
            if ',' in protocols:
                # e.g. "token, <token>"
                parts = [p.strip() for p in protocols.split(',')]
                for p in parts:
                    if p and not p.lower().startswith('token'):
                        return p
            else:
                return protocols.strip()

        return None

    def _validate_token_with_auth_service(self, token):
        """
        Call the PHP auth endpoint (AUTH_VALIDATE_FULL) with Authorization: Bearer <token>.
        Expect a 200 response with JSON payload containing user info (e.g., sub claim).
        Returns the parsed JSON payload on success, or None on failure.
        """
        http_client = tornado.httpclient.HTTPClient()
        try:
            req = tornado.httpclient.HTTPRequest(
                AUTH_VALIDATE_FULL,
                method='GET',
                headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'},
                request_timeout=5
            )
            resp = http_client.fetch(req)
            if resp.code != 200:
                logger.warning(f"auth service returned non-200: {resp.code}")
                return None
            body = resp.body.decode() if isinstance(resp.body, (bytes, bytearray)) else resp.body
            payload = json.loads(body)
            # Basic sanity checks: ensure payload contains a user identifier (sub or id)
            if isinstance(payload, dict) and ('sub' in payload or 'idUser' in payload or 'id' in payload or 'user' in payload):
                return payload
            # Some /me endpoints return { user: { ... } }
            if isinstance(payload, dict) and 'user' in payload and isinstance(payload['user'], dict):
                return payload['user']
            logger.warning("auth service payload missing expected user id")
            return None
        except tornado.httpclient.HTTPError as e:
            logger.warning("auth service HTTP error: " + str(e))
            return None
        except Exception as e:
            logger.error("auth service validation exception: " + str(e))
            return None
        finally:
            try:
                http_client.close()
            except:
                pass


##MAIN
#if __name__ == '__main__':
#    app = tornado.web.Application(handlers=[(r"/workHandler", SocketHandler)],debug = True, template_path = os.path.join(os.path.dirname(__file__), "templates"),static_path = os.path.join(os.path.dirname(__file__), "static"))
#    app.listen(8112)
#    tornado.ioloop.IOLoop.instance().start()