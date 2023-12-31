import React from "react";
import { useState, useEffect } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable, { tableInit } from '../Table/Table'
import { useFetchCamerasMutation} from '../../services/camerasService'
import { ITEM_LIST_DISPLAY_CNT } from '../../constants'


const CamerasListView: React.FC = () => {
    const [getCameras] = useFetchCamerasMutation()
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
    const [camerasDisplay, setCamerasDisplay] = useState<tableInit>(tableContentExample)

    const fetchCameras = async () => {
        try {
            const cameras = await getCameras({pageCount: page, pageSize: ITEM_LIST_DISPLAY_CNT}).unwrap()
            const newTable = {
                headers: ['Camera id', 'Name', 'User', 'Source parameters'],
                rows: cameras.map((camera) => {return [camera.idVideoSource.toString(), camera.name, camera.username, camera.sourceParameters]}),
                detailBtn: true,
                deleteBtn: true,
                editBtn: true,
                editCallback: handleShow
            } as tableInit
            setCamerasDisplay(newTable)
        } catch (error) {
            console.log(error);
        }
    }

    useEffect(() => {
        fetchCameras()
    },[page])
    
    return(
        <>
            <Modal show={show} onHide={handleClose}>
                <Modal.Header closeButton>
                    <Modal.Title>Camera details</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form>
                        <Form.Group className="mb-3" controlId="cameraDetails.name">
                            <Form.Label>camera id</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="id ..."
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="cameraDetails.name">
                            <Form.Label>camera name</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="node name ..."
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="cameraDetails.path">
                            <Form.Label>User</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="mode..."
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="cameraDetails.name">
                            <Form.Label>Source parameters</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="type ..."
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
                    <Col><BaseTable {...camerasDisplay}></BaseTable></Col>
                </Row>
            </Container>
        </>
    )
}

export default CamerasListView