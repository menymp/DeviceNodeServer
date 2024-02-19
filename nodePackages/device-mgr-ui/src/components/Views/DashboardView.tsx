import React from "react";
import { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable from '../Table/Table'
import { useNavigate } from "react-router-dom"
import { WEB_SOCK_SERVER_ADDR, SHOW_CONTROL_SIZE } from '../../constants'
import { 
    useFetchControlsMutation, 
    Control,
    controlTemplate
} from "../../services/dashboardService";
import { reactUIControlls } from '../../types/ControlTypes'
import DigitalOutput from './controls/DigitalOutput'

const DashboardView: React.FC = () => {
    const [show, setShow] = useState(false);
    const [page, setPage] = useState<number>(0);
    const navigate = useNavigate();
    const [getControls, {isSuccess: controlsLoaded, data: controls}] = useFetchControlsMutation();
    const [displayUIControls, setDisplayUIControls] = useState<reactUIControlls>();

    const handleClose = () => setShow(false);
    const handleShow = () => setShow(true);

    const ws = new WebSocket(WEB_SOCK_SERVER_ADDR);
    // const startVideoRef = useRef(false);
    // a pagination item already exists

    // ToDo: should i rearchitecture this moving the update responsability to each component, or should i
    // implement a central queue?

    // path to follow :
    // implement a component with all its UI and add it to a list, create a queue that will hold the user interaction commands
    // create an interval in the core component to process the user queued messages
    // each component will also provide an update command interface that will be send as a list to the backend side with the same
    // interval and thru the same socket, when the response arrives, the top component will forward to each of the list commponents
    // its response and each of them will handle the processing details.
    let currentCount = 0;
    let intervalsIds = [];
    let flagBussy = false; //flag used to indicate a pending response from wSocket
    let flagStop = 1; //ToDo: use this when the update process should not continue

    let controlsCommands = null;//holds the current visible controls
    let userCommands = []; //inmediate user command

    useEffect(() => {
        if (!controlsLoaded || !controls.length ) {
            return;
        }

        buildControlApperance(controls); // change for table logic
        initCommandsUpdate(); 
        commandScheduler(); //detonates the scheduler for the first time
                            //ToDo: what happens if a timeout and no response is received??
    }, [controlsLoaded, controls]);

    useEffect(() => {
        getControls({ pageCount: page, pageSize:  SHOW_CONTROL_SIZE });
    }, [page]);

    const ClearIntervalls = () => {
        for (var i = 0, len = intervalsIds.length; i < len; i++) 
        {
            clearInterval(intervalsIds[i]);
            intervalsIds[i] = null;
        }
    }


    const buildControlApperance = (receivedControls: Array<Control>) => {
        ClearIntervalls();
        $("#controlsContainer").empty();
        
        for (var i = 0, len = receivedControls.length; i < len; i++) 
        {
            const idLinkedDevice = parseInt((JSON.parse(receivedControls[i].parameters) as { idDevice: string }).idDevice);
            /*this is the proof of concept where each control has an object that defines apperance and behavior*/
            /*ToDo: better to refine this design before more complex controls arrive*/
            /*ToDo: since the device id is used as identifier, a new local id should be generated to handle
                    the cases where two controls such as switch and plain text share the same idDevice value*/
            if(receivedControls[i]["typename"] === "DIGITALOUTPUT")
            {
                const outputRef = useRef();
                const outputControl = <DigitalOutput ref={outputRef} commandHandler={commandHandler} control={receivedControls[i]}/>;
                setDisplayUIControls([...displayUIControls!, { idLinkedDevice: idLinkedDevice, component: outputControl, reference: outputRef }]);
            }
            if(receivedControls[i]["typename"] === "PLAINTEXT")
            {
                var controlClass = new ctrlPlainText(ctrlName, controlParameters);
                var ControlElementContainer = controlClass.constructUiApperance()
                $("#controlsContainer").append(ControlElementContainer);
                controls.push(controlClass);
                // var controlParameters = JSON.parse(data[i]["parameters"]);

                // var ControlElementContainer = document.createElement('form');
                // var ControlElementContainerText = document.createElement('label');
                // ControlElementContainer.innerHTML = data[i]["name"];
                // var textOut = document.createElement('label');
                    // textOut.setAttribute('class','text');
                // var tmpText = document.createElement('label');
                    // tmpText.setAttribute('type','textlabel');
                // tmpText.id = controlParameters["idDevice"];
                // textOut.appendChild(tmpText);
                // ControlElementContainer.appendChild(textOut);
                // $("#controlsContainer").append(ControlElementContainer);

                // let intervall = controlParameters["intervall"];
                // let iddev = controlParameters["idDevice"];
                // let cmdstr = controlParameters["readCmdStr"];
                // nIntervId = setInterval(commandHandler,intervall ,iddev, cmdstr);
                // intervalsIds.push(nIntervId);
            }
            if(receivedControls[i]["typename"] === "SENSORREAD")
            {
                
            }
            
        }
    }
    /* ToDo: these clases should instead be implemented as a component with UI and proper logic in it */
    /*single text apperance*/
    class ctrlPlainText
    {
        constructor(name, controlParameters)
        {
            this.name = name;
            this.idDevice = controlParameters["idDevice"];
            this.cmdUpdate = controlParameters["updateCmdStr"];
            this.cmdUpdateArgs = controlParameters["updateArgsStr"];
        }
        
        constructUiApperance()
        {
            var ControlElementContainer = document.createElement('form');
            var ControlElementContainerText = document.createElement('label');
            ControlElementContainer.innerHTML = this.name;
            var textOut = document.createElement('label');
            textOut.setAttribute('class','text');
            var tmpText = document.createElement('label');
            tmpText.setAttribute('type','textlabel');
            tmpText.id = this.idDevice;
            textOut.appendChild(tmpText);
            ControlElementContainer.appendChild(textOut);
            
            this.uiRefControl = tmpText;
            
            return ControlElementContainer;
        }
        
        update(response)
        {
            if(response.state === 'SUCCESS')
            {
                this.uiRefControl.innerHTML = ": '"+response.result+"'"
            }
        }
        /*ToDo: review if a best approach is to move this function to a super class*/
        getUpdateCommand()
        {
            var cmdObj = new Object();
            cmdObj.idDevice = parseInt(this.idDevice);
            cmdObj.command = this.cmdUpdate;
            cmdObj.args = ""; /*ToDo: check*/
            return cmdObj;
        }
    }

    /*
    control reference to the control
    idDevice 		id of the hardware device identifier
    controlParameters complete parameters
    updateCommand 	a valid command to get an state update
    updateArgs 		add args if expected from device
    updateCallback	a function to perform when a response is received
    */
    /*function addControlUpdateCmd(control, idDevice, updateCommand, controlParameters,  updateArgs, updateCallback)
    {
        var control = new Object();
        control.control = control; 
        control.idDevice = idDevice;
        control.controlParameters = controlParameters;
        control.command = updateCommand;
        control.args = updateArgs;
        control.updateCallback = updateCallback;
        controls.append(control);
    }*/

    const commandHandler = (deviceId, cmd, args) => {
        // var deviceId = caller.event.target.getAttribute('deviceId');
        //alert("command executed, device: "+deviceId + " cmd: "+ cmd);
        //var sString = "command executed, device: "+deviceId + " cmd: "+ cmd;
        var cmdObj = new Object();
        cmdObj.idDevice = deviceId;
        cmdObj.command = cmd;
        cmdObj.args = args; //ToDo: remember what the f*** is this field for
        // cmdObj.set('idDevice',deviceId);
        // cmdObj.set('command',cmd);
        // cmdObj.set('args','');
        //var jsonCmdStr = JSON.stringify(cmdObj);
        //alert(jsonCmdStr)
        
        //loads the collection with a new command
        userCommands.push(cmdObj);
        
        //ws_send(cmdObj);
    }

    const initCommandsUpdate = () => {
        cmds = []
        controls.forEach((controlClass)=>{
            var cmdObj = controlClass.getUpdateCommand();
            cmds.push(cmdObj);
        });
        var cmdsObj = new Object();
        cmdsObj.cmds = cmds;
        
        controlsCommands = JSON.stringify(cmdsObj);
    }
    //ToDo: initialize the array of controls
    //		based on controls array init commands array

    //this function is called continuously to update the UI
    //sends the current user input first to the wSocket and
    //cleans the interface, if no user input exists, sends 
    //the periodic control update status request.
    const commandScheduler = () => {
        //if user data
        var jsonStr;
        if(userCommands.length > 0)
        {
            var cmdsObj = new Object();
            cmdsObj.cmds = userCommands;
            jsonStr = JSON.stringify(cmdsObj);
            userCommands = [];
        }
        else
        {

            jsonStr = controlsCommands; //already stringified
        }
        ws_send(jsonStr);
        flagBussy = true;
    }

    const generateUpdateCommand = (parameter: {idDevice: string, cmdUpdate: string, args: string}) => {
                 const cmdObj: Record<string,string> = {};
                 cmdObj.idDevice = parseInt(parameter.idDevice);
                 cmdObj.command = parameter.cmdUpdate;
                 cmdObj.args = ""; /*ToDo: check*/
                 return cmdObj;
    }

    const responseHandler = (evt: Array<>) => {
        //alert(evt.data);
        //process the response
        var responses = JSON.parse(evt.data);
        
        responses.forEach((response) => {
            /*get the corresponding class of the response and updates it*/
            if (!displayUIControls || !displayUIControls.length) {
                return
            }
            const tmpUIcontrol = displayUIControls.filter((uiControl) => uiControl.idLinkedDevice == response.idDevice);
            tmpUIcontrol[0].reference.current?.update(response);
        });
        
        setTimeout(() => {
            if(flagStop == 1)//ToDo: define flag stop
            {
                commandScheduler();
            }
        }, 1000);	//define this time elsewhere
        flagBussy = false;
    }

    const ws_send = (msg) => {
    // if( websocket == true ){
        // if ws is not open call open_ws, which will call ws_send back
        if( typeof(ws) == 'undefined' || ws.readyState === undefined || ws.readyState > 1) {
            open_ws(msg);
            }else{
            ws.send( JSON.stringify(msg) );
            console.log("ws_send sent");
        }
    // }
    }


    const open_ws = (msg) => {
        if( typeof(ws) == 'undefined' || ws.readyState === undefined || ws.readyState > 1){
            // websocket on same server with address /websocket
            
            ws.onopen = function(){
                // Web Socket is connected, send data using send()
                console.log("ws open");
                if( msg.length != 0 ){
                        //ws_send(msg);
                    }
                };
            ws.onmessage = function(evt) {
                    responseHandler(evt);
            }
            // ws.onmessage = function (evt){
                // var received_msg = evt.data;
                // console.log(evt.data);
                    // msg = JSON.parse(evt.data)

                // if( msg.event == "x" ){
                // // process message x
                // }else if( msg.event == 'y' ){
                // // process message y
                // }else if( msg.event == 'z' ) {
                // // process message z
                // }
            // };

            // ws.onclose = function(){ 
                // // websocket is closed, re-open
                // console.log("Connection is closed... reopen");
            // var msg = { event: 'register', };
            // setTimeout( function(){ws_send(msg);}, 1000 );
            // };
        }
    }

    return(
        <>
            <Modal show={show} onHide={handleClose}>
                <Modal.Header closeButton>
                    <Modal.Title>Dashboard control</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form>
                        <Form.Group className="mb-3" controlId="deviceDetails.name">
                            <Form.Label>device id</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="id ..."
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="deviceDetails.name">
                            <Form.Label>device name</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="node name ..."
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="deviceDetails.path">
                            <Form.Label>Mode</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="mode..."
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="deviceDetails.name">
                            <Form.Label>type</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="type ..."
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="deviceDetails.path">
                            <Form.Label>device path</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="/devicePath/..."
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="deviceParentNode.name">
                            <Form.Label>parent node</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="parent node ..."
                                autoFocus
                            />
                        </Form.Group>
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={handleClose}>
                        Close
                    </Button>
                </Modal.Footer>
            </Modal>
            <Container >
                <Row className="p-3 mb-2 bg-success bg-gradient text-white rounded-3">
                    <Col xs={2}>
                        <Button onClick={() => navigate('/DashboardEditor')}>Editor</Button>
                    </Col>
                    <Col>
                        <Form className="mr-left ">
                            <Form.Group className="mb-3 form-check-inline" controlId="searchFilterField">
                                <Row xs={12}>
                                    <Col xs={6}>
                                        <Button onClick={() => {
                                            if (page == 0) {
                                                return;
                                            }
                                            setPage(page - 1);
                                        }}>Previous page</Button>
                                    </Col>
                                    <Col xs={1}>
                                        <Form.Label> 10 </Form.Label>
                                    </Col>

                                    <Col  xs={5}>
                                        <Button onClick={() => {
                                            setPage(page + 1);
                                        }}>Next page</Button>
                                    </Col>
                                </Row>
                            </Form.Group>
                        </Form>
                    </Col>
                </Row>
                <Row>
                    <Container id="controlsUIContainer">
                        {displayUIControls?.map((uiControl) => { return uiControl.component })}
                    </Container>
                </Row>
            </Container>
        </>
    )
}

export default DashboardView