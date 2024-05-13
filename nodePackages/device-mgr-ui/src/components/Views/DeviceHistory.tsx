import React from "react";
import { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable, { tableInit } from '../Table/Table'
import { useFetchDevicesMutation, useFetchDeviceByIdMutation, device } from '../../services/deviceService'
import { ITEM_LIST_DISPLAY_CNT } from '../../constants'
import useControlUtils from "../../hooks/useControlUtils";
import { 
    GenericUIControlParameters, 
    updateResponse
} from '../../types/ControlTypes'

export type DeviceHistoryParameters = {
    idDevice: string,
    ws: WebSocket
}

type GetHistoryParameters = {
    idDevice: string, 
    servercommand: string
}

const DeviceHistory = ({ws, idDevice}: DeviceHistoryParameters) => {
    const [getDeviceById, {isSuccess: selectedDeviceFound, data: matchDevices}] = useFetchDeviceByIdMutation()

    useEffect(() => {
        getDeviceById({deviceId: parseInt(idDevice)});

    },[])

    const getControlParameters = () => {
        return {idDevice, servercommand: "getMeasures"} as GetHistoryParameters;
    }

    const update = (response: updateResponse) => {
        ///////////////////////////////////////
        /** begins user specific code * */
        const { servercommand } = getControlParameters()
        let check = false;
        if(response.syscommand !== servercommand)
        {
            //discard all unrelated messages
            return
        }
        if(response.state === 'SUCCESS')
        {
            // decode the expected history
        }
        /* ends user specific code */
        //////////////////////////////////////////////////
    }

    const { commandHandler } = useControlUtils({ getControlParameters, ws, update});
    
    return(
        <>
            <Modal show={show} onHide={handleClose}>
                <Modal.Header closeButton>
                    <Modal.Title>Device details</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form>
                        <Form.Group className="mb-3" controlId="deviceDetails.name">
                            <Form.Label>device id</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="Device id ..."
                                autoFocus
                                readOnly
                                defaultValue={deviceDetail?.idDevices}
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="deviceDetails.name">
                            <Form.Label>device name</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="name ..."
                                autoFocus
                                readOnly
                                defaultValue={deviceDetail?.name}
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="deviceDetails.path">
                            <Form.Label>Mode</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="mode..."
                                autoFocus
                                readOnly
                                defaultValue={deviceDetail?.mode}
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="deviceDetails.name">
                            <Form.Label>type</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="type ..."
                                autoFocus
                                readOnly
                                defaultValue={deviceDetail?.type}
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="deviceDetails.path">
                            <Form.Label>device path</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="/devicePath/..."
                                autoFocus
                                readOnly
                                defaultValue={deviceDetail?.channelPath}
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="deviceParentNode.name">
                            <Form.Label>parent node</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="parent node..."
                                autoFocus
                                readOnly
                                defaultValue={deviceDetail?.nodeName}
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
                    <Col xs={5} >
                        <Form className="mr-left ">
                            <Form.Group className="mb-3 form-check-inline" controlId="searchFilterField">
                                <Row xs={12}>
                                    <Col xs={2}>
                                        <Form.Label>Filter</Form.Label>
                                    </Col>
                                    <Col xs={5}>
                                        <Form.Control type="text" placeholder="node name..." onChange={handleChangeFilterNodeName}/>
                                    </Col>
                                    <Col xs={5}>
                                        <Form.Control type="text" placeholder="parent node..." onChange={handleChangeFilterName}/>
                                    </Col>
                                </Row>
                            </Form.Group>
                        </Form>
                    </Col>
                    <Col>
                        <Form className="mr-left ">
                            <Form.Group className="mb-3 form-check-inline" controlId="searchFilterField">
                                <Row xs={12}>
                                    <Col xs={6}>
                                        <Button onClick={() => {(page > 0) && setPage(page - 1)}}>Previous page</Button>
                                    </Col>
                                    <Col xs={1}>
                                        <Form.Label>{page}</Form.Label>
                                    </Col>
                                    <Col xs={5}>
                                        <Button onClick={() => {setPage(page + 1)}}>Next page</Button>
                                    </Col>
                                </Row>
                            </Form.Group>
                        </Form>
                    </Col>
                </Row>
                <Row>
                    <Col><BaseTable {...devicesDisplay}></BaseTable></Col>
                </Row>
            </Container>
        </>
    )
}

export default DeviceHistory