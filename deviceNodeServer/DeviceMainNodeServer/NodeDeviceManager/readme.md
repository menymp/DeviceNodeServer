NodeDeviceManager
-this service keeps the devices channels updated.
-each of the new nodes that are inserted in the nodes tables are scanned and each of its child devices are added

below a description and a definition of the classes available

'nodeDeviceDiscoveryTool' serves as a discovery tool to retrive the data from new nodes that were added to the current nodes list, it will retrive the manifest for each of the nodes based on its manifest main path and create all the devices available as a record in a db table.
below are the members of the server:
- 'initNodeParameters' init the db data connection, as well as its args
- 'stop' stops a search request
- 'getState' gets the state of the current discovery instance
- 'addDiscoveredChildDevice' adds a new discovered device, this is used by the listener as a callback
- 'discoveryListenerDone' updates the current state to DONE when a discovery was acomplished

'mqttNodeListener' this class handles the request protocol with devices that uses MQTT. below a list of the members for the class
- 'init' inits the listener
- 'startMqttClient' starts the current client class search
- 'clientlisten' listen for an available channel in a given node
- 'stop' stops a current device discovery
- 'on_Manifestmessage' callback for when a message was received
- 'on_Devconnect' callback for when a device connection happens
- 'listenDeviceChannel' listens for a device channel once the discovery happens
- 'allDevicesFound' indicates when all devices were found with success
- 'deviceAlreadyFound' determines if a device was already found

'nodeDeviceManager' this class handles the discovery and performs the search request in a periodic manner. Its also responsible for the db request to insert new discovered devices. below are its members.
- 'getNodes' gets all the nodes registered for the db
- 'getState' gets the discovery instance current state
- 'discoverNodeDevices' performs the discovery of child devices for the devices found
- 'taskWaitForDiscovery' wait for the device discovery to finish
- 'stop' stops the current device search
- 'registerNodes' register the discovered devices for the given nodes.
