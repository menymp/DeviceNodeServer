DeviceManager

- manages all the asociated devices and perform command send and receive

This server handles the device command and response communication.

'deviceManager' class is the entry point for the commands, newer user devices will be added to the current
data as soon as the load process starts again, this refresh is performed by 'startLoadDevices' and the process will be triggered
each 10 seconds by default.

below are the methods available for deviceManager class
- 'init'
- 'updateMeasuresWorker'
- 'deviceLoad'
- 'updateDeviceMeasure'
- 'deviceAlreadyInit'
- 'cleanOldDevices'
- 'executeCMDJson'
- 'executeCMD'
- 'executeCMDraw'
- 'execCommand'

'device' class abstracts each available device detected by the search process of 'DeviceManager' main instance
below are the method descriptions
- 'init'
- 'writeDeviceMeasure'
- '__del__'
- 'getValue'
- 'initDriver'
- 'executeCMD'

each 'device' instance class contains a driver instance depending on the accepted protocol of communication between the
hardware device and the current server instance, at the moment only mqtt protocol is cupported, but in the future is expected
to also handle 'socket' communication.
below are the method descriptions

'mqttDriver' class abstracts the mqtt driver device communication and is based on the paho.mqtt mqtt library
below are the method descriptions
- 'init'
- 'stop'
- 'getLockFlag'
- 'initDriver'
- 'clientlisten'
- 'sendCommand'
- 'getValue'
- 'on_connect'
- 'on_message'




