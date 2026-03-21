This server works as a new approach


The idea is to have all the clients communicate to the server perpetualy with its name and the mac address


the dynamics are the following:

1- ESP32 Inits and attempts to connect to the server

2- Server accepts the connection for esp32

3- ESP32 The esp32 begins the data trasmission by providing the camera name followed by a # delimitator 
   followed by the fixed len of the mac address followed by a second delimitator and finally the JPG image capture from the camera

4- server attempts to decode the following args with a timeout, then identifies the device mac and the camera and store them in the DB

5- server attempts to read the camera frame and decode into np array

6- the frame can then be read by the tornado server when needed
