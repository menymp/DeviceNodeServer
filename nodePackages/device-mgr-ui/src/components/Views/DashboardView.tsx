import React from "react";
import { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Button, Form, Modal, Card, Figure } from 'react-bootstrap';
import BaseTable from '../Table/Table';
import { useNavigate } from "react-router-dom";
import { WEB_SOCK_SERVER_ADDR, SHOW_CONTROL_SIZE } from '../../constants';
import { 
    useFetchControlsMutation, 
    Control,
    controlTemplate
} from "../../services/dashboardService";
import { reactUIControll, deviceCommand, CONTROL_TYPE} from '../../types/ControlTypes';
import DigitalOutput from './controls/DigitalOutput';
import PlainText from "./controls/PlainText";
import SensorRead from "./controls/SensorRead";
import DigitalInput from "./controls/DigitalInput";
import TextSender from "./controls/TextSender"
import { CONTROLS_COLUMN_NUM, DISPLAY_CONTROLS_NUM } from '../../constants';
import { create } from "domain";
import { v4 as uuid } from 'uuid';

const DashboardView: React.FC = () => {
    const [show, setShow] = useState(false);
    const [page, setPage] = useState<number>(0);
    const navigate = useNavigate();
    const [getControls, {isSuccess: controlsLoaded, data: controls}] = useFetchControlsMutation();
    const [displayUIControls, setDisplayUIControls] = useState<Array<reactUIControll>>([]);
    const [controlsGrid, setControlsGrid] = useState<Array<React.ReactElement>>([]);

    const handleClose = () => setShow(false);

    let ws = useRef<WebSocket|null>();

    useEffect(() => {
        ws.current = new WebSocket(WEB_SOCK_SERVER_ADDR);
        ws.current.onopen = () => console.log("ws opened");
        ws.current.onclose = () => console.log("ws closed");

        const wsCurrent = ws.current;

        return () => {
            wsCurrent.close();
        };
    }, []);

    useEffect(() => {
        if (!controlsLoaded || !controls || !controls.length || !ws || ws.current?.readyState !== WebSocket.OPEN) {
            return;
        }

        buildControlApperance(controls); // change for table logic
    }, [controlsLoaded, controls, ws.current?.readyState]);

    useEffect(() => {
        getControls({ pageCount: page*DISPLAY_CONTROLS_NUM, pageSize:  DISPLAY_CONTROLS_NUM });
    }, [page]);

    useEffect(() => {
        if (!displayUIControls?.length) {
            return;
        }
        createComponentsGrid();
    }, [displayUIControls]);

    const createComponentsGrid = () => {
        /* ToDo: this will be calculated with the screen length */
        const numColumns = CONTROLS_COLUMN_NUM;
        const rows = [] as Array<React.ReactElement>;
        for (let i = 0; i < numColumns; i++) {
          const cols = [];
          for (let j = 0; j < numColumns; j++) {
            const index = i * numColumns + j;
            if (index >= displayUIControls?.length) {
                rows.push(<Row key={i}>{cols}</Row>);
                setControlsGrid(rows)
                return;
            }
            const controlUi = displayUIControls[index].component
            cols.push(
                <div key={i} className="square-container" style={{ 
                    margin: '5px', 
                    padding: '10px', 
                    borderRadius:'25px', 
                    display: 'flex', 
                    justifyContent: 'center', 
                    alignItems: 'center',
                    border: '2px solid transparent', 
                    backgroundColor: 'gray', 
                    width: '200px', 
                    height: '200px' 
                    }}><Col key={index} xs={12} md={6} lg={4}>
                {controlUi}
              </Col>
              </div>
            );
          }
          rows.push(<Row key={i}>{cols}</Row>);
        }
    }


    const buildControlApperance = (receivedControls: Array<Control>) => {
        if (!ws.current) {
            return;
        }
        let tmpControls = [] as Array<any>;
        setDisplayUIControls([]);
        
        for (var i = 0, len = receivedControls.length; i < len; i++) 
        {
            const idLinkedDevice = parseInt((JSON.parse(receivedControls[i].parameters) as { idDevice: string }).idDevice);
            let outputControl;
            var id: string = uuid();
            const controlTypeName = receivedControls[i]["typename"]
            if(controlTypeName === CONTROL_TYPE.DIGITALOUTPUT)
            {
                outputControl = <DigitalOutput ws={ws.current} control={receivedControls[i]} id={id}/>;
            }
            if(controlTypeName === CONTROL_TYPE.PLAINTEXT)
            {
                outputControl = <PlainText ws={ws.current} control={receivedControls[i]} id={id}/>;
            }
            if(controlTypeName === CONTROL_TYPE.SENSORREAD)
            {
                outputControl = <SensorRead ws={ws.current} control={receivedControls[i]} id={id}/>;
            }
            if(controlTypeName === CONTROL_TYPE.DIGITALINPUT)
            {
                outputControl = <DigitalInput ws={ws.current} control={receivedControls[i]} id={id}/>;
            }
            if(controlTypeName === CONTROL_TYPE.TEXTSENDER)
            {
                outputControl = <TextSender ws={ws.current} control={receivedControls[i]} id={id}/>;
            }
            outputControl && tmpControls.push({ idLinkedDevice: idLinkedDevice, component: outputControl });
        }
        setDisplayUIControls(tmpControls);
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
                        {controlsGrid}
                    </Container>
                </Row>
            </Container>
        </>
    )
}

export default DashboardView