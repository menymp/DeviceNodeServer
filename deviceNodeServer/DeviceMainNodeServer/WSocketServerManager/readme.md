'WSocketServerManager'

- handles the request response from the React main UI for the websocket communication

'handleOnMessage' class will create a connector interface between deviceManager process server and the current websocket server
once a connection is established, the web UI will start sending the request commands in the following form
```
        cmd = {
            "method":"executeCMDJson",
            "arg":"{json command obj ...}"
        }
```
the command will be sent with a zmq socket connection to the deviceManager interface and expect a response in return with the result of
the executed commands for each of the id devices. the callback for a new websocket message from the UI is 'on_MessageCmd', this receives the command in
the expected form and returns the result of the current execution.

'wSocketServerManager' contains the main logic for the websocket server that handles the UI connection and the websocket command requests and responses.
the request response behavior is defined in 'SocketHandler' class
the following are the most important methods
- 'init': inits the class port for the websocket handling
- 'serverListen': this will start the listener server, as an arg it receives on_MessageCmd as a callback that will be called for each of the received messages from UI
- 'stop': stops the current server instance

'SocketHandler' the server implements the websocket request response behavior
- 'on_message' is called when a client send its data. and return the repsonse with 'write_message' method
- 'check_origin' is used for the origin comprobation, ToDo: implement properly this instead of returning true by default