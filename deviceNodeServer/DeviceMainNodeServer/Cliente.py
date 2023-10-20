# client.py

import socket                   # Import socket module
from io import BytesIO
from PIL import Image
import cv2
import numpy as np

#s = socket.socket()             # Create a socket object
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# host = '####'     # Get local machine name
# port = 8072 

# s.connect((host, port))
# s.send(b"k") #comando de captura

#f = BytesIO()

while 1:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '####'     # Get local machine name
    port = 8072                    # Reserve a port for your service.

    s.connect((host, port))
    s.send(b"k") #comando de captura
    f = BytesIO()
    
    while True:
        #print('receiving data...')
        data = s.recv(1024)
        #print('data=%s', (data))
        if not data:
            f.seek(0)
            break
        # write data to a file
        f.write(data)

    # with BytesIO() as f:
        # print('file opened')
        # while True:
            # print('receiving data...')
            # data = s.recv(1024)
            # #print('data=%s', (data))
            # if not data:
                # f.seek(0)
                # break
            # # write data to a file
            # f.write(data) 
    # print("input bytes = "+ str(f.getbuffer().nbytes))
    #img = Image.open(f)
    #img.show()
    #print('done #################################################################')
    s.close()
    img = cv2.imdecode(np.frombuffer(f.read(), np.uint8), 1)
    
    # scale_percent = 60 # percent of original size
    # width = int(img.shape[1] * scale_percent / 100)
    # height = int(img.shape[0] * scale_percent / 100)
    # dim = (width, height)
    
    img2 = cv2.resize(img,(900,800),interpolation = cv2.INTER_AREA)
    
    cv2.imshow("img", img)
    cv2.waitKey(10)
    #sr = input("press key")

print('Successfully get the file')

# while 1:
    # try:
        # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # host = '192.168.1.128'     # Get local machine name
        # port = 8072 

        # s.connect((host, port))
        # s.send(b"k") #comando de captura
        # with open('received_file.jpg', 'wb') as f:
            # print('file opened')
            # while True:
                # print('receiving data...')
                # data = s.recv(1024)
                # #print('data=%s', (data))
                # if not data:
                    # break
                # # write data to a file
                # f.write(data)
        # s.close()
        # img = cv2.imread('received_file.jpg', 0)

        # cv2.imshow("img", img)
        # cv2.waitKey(10)
    # except:
        # pass
    # sr = input("press key")

# f.close()
# s.close()
# img = Image.open('received_file.jpg')
# img.show()
s.close()
print('connection closed')
input('press any key to finish')


