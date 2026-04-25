#This works
#for some reason the default example with devices does not work, using RemoteXbeeDevice worked

from digi.xbee.devices import XBeeDevice, RemoteXBeeDevice
from digi.xbee.models.address import XBee64BitAddress

# Instantiate a local XBee node.
xbee = XBeeDevice("COM8", 9600)
xbee.open()

# Instantiate a remote XBee node.
remote = RemoteXBeeDevice(xbee, XBee64BitAddress.from_hex_string("sss"))

# Send data using the remote object.
xbee.send_data(remote, "Hello XBee sss!")