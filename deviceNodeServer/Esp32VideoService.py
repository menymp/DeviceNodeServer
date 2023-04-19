from threading import Thread
from threading import Lock
from threading import Event
import socket                   # Import socket module
from io import BytesIO
import cv2


class Esp32VideoService():
	def __init__(self, connectionArgs):
		self.host = connectionArgs["host"]
		self.port = connectionArgs["port"]
		pass
	
	def start():
		self.stopEvent = Event()
		self.taskUpdateImage = Thread(self._taskUpdateImage, args = (self.host, self.port, self.stopEvent)
		self.taskUpdateImage.start()
		pass
	
	def stop():
		if self.stopEvent:
			self.stopEvent.set()
		pass
	
	def _taskUpdateImage(self, host, port, closeEvent):
		# Reserve a port for your service.
		#ToDo: review for better approach than connect and disconect.
		while not closeEvent.is_set()
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((host, port))
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
	
	def _updateImage(self, image):
		self.spinLockComm.acquire()
		self.image = image
		self.spinLockComm.release()
	
	def getImage(self):
		self.spinLockComm.acquire()
		imageTmp = self.image
		self.spinLockComm.release()
		return imageTmp