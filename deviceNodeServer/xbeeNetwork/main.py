'''
Network adapter for device manager system and xbee shield
menymp

this app works as a sub register that allow receiving and transfer of
data from and to xbee network.

The application starts with a discovery of each device and creates a list of devices.
this is performed periodicaly and allow to incorporate new devices into the network.

with the existing devices, a manifest is then created in the same way as other mqtt devices

then each device information is forward relayed to a subtopic for publisher and subscribers
in the case of subscribers, an aditional subscription is created in order to accept incomming commands.


In construction ...
'''

import time
import threading
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from digi.xbee.models.status import NetworkDiscoveryStatus
from digi.xbee.devices import XBeeDevice


# TODO: Replace with the serial port where your local module is connected to.
PORT = "COM1"
# TODO: Replace with the baud rate of your local module.
BAUD_RATE = 9600

manifest = {
        "Name":"ID OF THE EXPECTED NETWORK",
        "RootName":"/MenyGasNode1/",
        "Devices":["MQ3","MQ4","MQ6","MQ7","MQ8","MQ135"] #
}
jsonManifest = json.dumps(manifest)

class mqttDriver():
    def init(self, args, path = ""):
        self.subscriberPath = path
        self.connArgs = json.loads(args)
        self.initDriver()
        self.value = ""
        self.lastSentCmd = ""
        self.lockUpdateFlag = False
        #self.initDriver()
        pass
    #locks the result until a new response is sent
    #since the backend is designed in this way this should
    #mitigate the effect of the delayed update
    def getLockFlag(self):
        return self.lockUpdateFlag

    def initDriver(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.connArgs["broker"], self.connArgs["port"], self.connArgs["keepalive"])

        taskListen = threading.Thread(target=self.clientlisten, args=(self.client,))
        taskListen.start()
        pass

    def clientlisten(self, arg):
        arg.loop_forever()
        pass

    def sendCommand(self,command, args):
        self.lockUpdateFlag  = True
        self.lastSentCmd = command
        publish.single(topic = args, payload = command, hostname = self.connArgs["broker"])
        pass

    def getValue(self):
        return self.value

    def on_connect(self, client, userdata, flags, rc):
        if self.subscriberPath == "":
            return
        self.client.subscribe(self.subscriberPath)
        pass

    def on_message(self, client, userdata, msg):
        m_decode=str(msg.payload.decode("utf-8","ignore"))
        data = json.loads(m_decode)
        self.value = data["Value"]
        if self.lockUpdateFlag and self.lastSentCmd == self.value: #ToDo: a race condition may happens if no update received
            self.lockUpdateFlag = False
        pass

def discoveryDevices():
    print("scanning Xbee network for available devices")

    device = XBeeDevice(PORT, BAUD_RATE)

    try:
        device.open()
        xbee_network = device.get_network()
        xbee_network.set_discovery_timeout(15)  # 15 seconds.
        xbee_network.clear()

        # Callback for discovered devices.
        def callback_device_discovered(remote):
            print("Device discovered: %s" % remote)

        # Callback for discovery finished.
        def callback_discovery_finished(status):
            if status == NetworkDiscoveryStatus.SUCCESS:
                print("Discovery process finished successfully.")
            else:
                print("There was an error discovering devices: %s" % status.description)

        xbee_network.add_device_discovered_callback(callback_device_discovered)

        xbee_network.add_discovery_process_finished_callback(callback_discovery_finished)

        xbee_network.start_discovery_process()

        print("Discovering remote XBee devices...")

        while xbee_network.is_discovery_running():
            time.sleep(0.1)

    finally:
        if device is not None and device.is_open():
            device.close()


#ToDo: add mqtt manifest callback for compliance with devices
#each device will create a channel under mqtt standard broker
if __name__ == '__main__':
    pass