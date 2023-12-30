import React from "react";
import { useState, useEffect } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable, { tableInit } from '../Table/Table'
import { useFetchDevicesMutation } from '../../services/deviceService'
import { ITEM_LIST_DISPLAY_CNT } from '../../constants'


const DevicesListView: React.FC = () => {
    const [getDevices] = useFetchDevicesMutation()
    const [show, setShow] = useState(false);

    const handleClose = () => setShow(false);
    const handleShow = () => setShow(true);

    const tableContentExample = {
        headers: ["header1", "header2", "header3", "header4"],
        rows: [["1val1", "1val2", "1val3", "1var4"],["2val1", "2val2", "2val3", "2vr4"],["3val1", "3val2", "3val3","3var5"]],
        detailBtn: true,
        detailCallback: handleShow
    }
    // a pagination item already exists

    const [page, setPage] = useState<number>(0)
    const [devicesDisplay, setDevicesDisplay] = useState<tableInit>(tableContentExample)

    const fetchDevices = async () => {
        try {
            const devices = await getDevices({pageCount: page, pageSize: ITEM_LIST_DISPLAY_CNT}).unwrap()
            const newTable = {
                headers: ['Device id', 'Name', 'Mode', 'Type', 'Path', 'Parent node'],
                rows: devices.map((device) => {return [device.idDevices.toString(), device.name, device.mode, device.type, device.channelPath, device.nodeName]}),
                detailBtn: true,
                deleteBtn: true,
                editBtn: true,
                editCallback: handleShow
            } as tableInit
            setDevicesDisplay(newTable)
        } catch (error) {
            console.log(error);
        }
    }

    useEffect(() => {
        fetchDevices()
    },[page])
    
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
                    <Col xs={5} >
                        <Form className="mr-left ">
                            <Form.Group className="mb-3 form-check-inline" controlId="searchFilterField">
                                <Row xs={12}>
                                    <Col xs={2}>
                                        <Form.Label>Filter</Form.Label>
                                    </Col>
                                    <Col xs={5}>
                                        <Form.Control type="text" placeholder="node name..." />
                                    </Col>
                                    <Col xs={5}>
                                        <Form.Control type="text" placeholder="parent node..." />
                                    </Col>
                                </Row>
                            </Form.Group>
                        </Form>
                    </Col>
                    <Col>
                        <Form className="mr-left ">
                            <Form.Group className="mb-3 form-check-inline" controlId="searchFilterField">
                                <Row xs={12}>
                                    <Col xs={5}>
                                        <Button onClick={() => {setPage(page + 1)}}>Next page</Button>
                                    </Col>
                                    <Col xs={1}>
                                        <Form.Label>{page}</Form.Label>
                                    </Col>
                                    <Col xs={6}>
                                        <Button onClick={() => {(page > 0) && setPage(page - 1)}}>Previous page</Button>
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

export default DevicesListView