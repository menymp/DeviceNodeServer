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
import { reactUIControlls, deviceCommand } from '../../types/ControlTypes'
import DigitalOutput from './controls/DigitalOutput'
import { POLL_INTERVAL_MS } from '../../constants'

// ToDo: change of approach, each component will send its individual command to the websocket
//       and receive and decode only the received messages that contain the control id
const DashboardView: React.FC = () => {
    const [show, setShow] = useState(false);
    const [page, setPage] = useState<number>(0);
    const navigate = useNavigate();
    const [getControls, {isSuccess: controlsLoaded, data: controls}] = useFetchControlsMutation();
    const [displayUIControls, setDisplayUIControls] = useState<reactUIControlls>();
    const [userCommands, setUserCommands] = useState<Array<deviceCommand>>([]);
    const [controlsCommands, setControlCommands] = useState<string>('');
    const [flagBussy, setFlagBussy] = useState<boolean>(false);

    const handleClose = () => setShow(false);
    const handleShow = () => setShow(true);

    const ws = new WebSocket(WEB_SOCK_SERVER_ADDR);
    
    ws.onopen = () =>{
        // Web Socket is connected, send data using send()
        console.log("ws open");
    };
    // data from websocket received
    ws.onmessage = (evt) => {
            responseHandler(evt);
    }
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
    let flagStop = 1; //ToDo: use this when the update process should not continue

    useEffect(() => {
        if (!controlsLoaded || !controls.length ) {
            return;
        }

        buildControlApperance(controls); // change for table logic
        initCommandsUpdate(); 
        commandScheduler(); //detonates the scheduler for the first time
                            //ToDo: what happens if a timeout and no response is received??
                            //      to prevent this implement a second schedule to act as a watchdog
    }, [controlsLoaded, controls]);

    useEffect(() => {
        getControls({ pageCount: page, pageSize:  SHOW_CONTROL_SIZE });
    }, [page]);

    const ClearIntervalls = () => {
        for (var i = 0, len = intervalsIds.length; i < len; i++) 
        {
            // clearInterval(intervalsIds[i]);
            // intervalsIds[i] = null;
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

    const commandHandler = (deviceId: number, cmd: string, args: string) => {
        //loads the collection with a new command
        userCommands.push(generateUpdateCommand(deviceId, cmd, args));
    }

    const initCommandsUpdate = () => {
        if (!controls?.length) {
            return;
        }

        let cmds: Array<deviceCommand> = [];
        controls.forEach((controlToDisplay)=>{
            const { updateCmdStr, idDevice, args } = JSON.parse(controlToDisplay.parameters) as { updateCmdStr: string, idDevice: string, args: string }
            cmds.push(generateUpdateCommand(parseInt(idDevice), updateCmdStr, args));
        });
        
        setControlCommands(JSON.stringify({ cmds: cmds }));
    }
    //ToDo: initialize the array of controls
    //		based on controls array init commands array

    //this function is called continuously to update the UI
    //sends the current user input first to the wSocket and
    //cleans the interface, if no user input exists, sends 
    //the periodic control update status request.
    const commandScheduler = () => {
        //if user data
        let jsonStr = "";
        if(userCommands.length > 0)
        {
            jsonStr = JSON.stringify({ cmds: userCommands });
            setUserCommands([]);
        }
        else
        {

            jsonStr = controlsCommands; //already stringified
        }
        ws_send(jsonStr);
        setFlagBussy(true);
    }

    const generateUpdateCommand = (idDevice: number, cmdUpdate: string, args: string):deviceCommand => {
        return {
            idDevice: idDevice,
            command: cmdUpdate,
            args: args
        }
    }

    const responseHandler = (evt: any) => {
        //process the response
        const responses = JSON.parse(evt.data);
        
        responses.forEach((response: any) => {
            /*get the corresponding class of the response and updates it*/
            if (!displayUIControls || !displayUIControls.length) {
                return
            }
            const tmpUIcontrol = displayUIControls.filter((uiControl) => uiControl.idLinkedDevice === response.idDevice);
            tmpUIcontrol[0].reference.current?.update(response);
        });
        
        setTimeout(() => {
            if(flagStop == 1)//ToDo: define flag stop
            {
                commandScheduler();
            }
        }, POLL_INTERVAL_MS);
        setFlagBussy(false);
    }

    const ws_send = (msg: any) => {
        if( typeof(ws) == 'undefined' || ws.readyState === undefined || ws.readyState > 1) {
            console.error('error websocket is closed');
        }
        ws.send( JSON.stringify(msg) );
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