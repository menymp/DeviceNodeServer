#simple pc test device for send and receive data
#ai generated code for testing 

# Import the serial module
import serial
from threading import Thread
import time
from digi.xbee.devices import XBeeDevice, RemoteXBeeDevice
from digi.xbee.models.address import XBee64BitAddress

# Instantiate a local XBee node.
xbee = XBeeDevice("COM7", 9600)
xbee.open()

# Instantiate a remote XBee node.
remote = RemoteXBeeDevice(xbee, XBee64BitAddress.from_hex_string(""))

# Define a function to send a string every 6 seconds
def send_string():
    while True:
        xbee.send_data(remote, "humidity,1")
        print("Sent data: " + "humidity,1")
        time.sleep(6)

# Start the function
tSend = Thread(target=send_string)
tSend.start()

# Create an infinite loop to check for bytes to read
def data_receive_callback(xbee_message):
    print("From %s >> %s" % (xbee_message.remote_device.get_64bit_addr(), xbee_message.data.decode()))

xbee.add_data_received_callback(data_receive_callback)

while True:
    pass