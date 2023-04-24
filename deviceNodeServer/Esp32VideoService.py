import socket                   # Import socket module
from io import BytesIO
import cv2
import numpy as np
from BaseVideoService import BaseVideoService

class Esp32VideoService(BaseVideoService):
	def _taskUpdateImage(self, connectionArgs):
		# Reserve a port for your service.
		#ToDo: review for better approach than connect and disconect.
		#	   in the near future maybe never, check for a better approach for this case
		while not self.stopEvent.is_set():
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((connectionArgs["host"], connectionArgs["port"]))
			s.send(b"k") #comando de captura
			f = BytesIO()
			while True:
				data = s.recv(1024)
				if not data:
					f.seek(0)
					break
				f.write(data)
			
			s.close()
			img = cv2.imdecode(np.frombuffer(f.read(), np.uint8), 1)
			#cv2.imshow("img", img)
			#cv2.waitKey(10)
			self._updateImage(img)
#test code
#http://#####:8072/video
#    connArgs = {"host": '192.168.1.99', "port": 8072}
#    cam = Esp32VideoService(connArgs)
#    cam.start()