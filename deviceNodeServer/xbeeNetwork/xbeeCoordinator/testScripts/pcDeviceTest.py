#simple pc test device for send and receive data
#ai generated code for testing 
#Instead of being always publishing values, we reply for each request from data

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
#remote = RemoteXBeeDevice(xbee, XBee64BitAddress.from_hex_string(""))
# Create an infinite loop to check for bytes to read
def data_receive_callback(xbee_message):
    print("From %s >> %s" % (xbee_message.remote_device.get_64bit_addr(), xbee_message.data.decode()))
    # Instantiate a remote XBee node.
    remote = RemoteXBeeDevice(xbee, xbee_message.remote_device.get_64bit_addr())
    xbee.send_data_async(remote, "humidity,1")
    print("Sent data: " + "humidity,1")

xbee.add_data_received_callback(data_receive_callback)

while True:
    pass