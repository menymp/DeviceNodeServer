import React from "react";
import { useState } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable from '../Table/Table'
import { useNavigate } from "react-router-dom"


const DashboardView: React.FC = () => {
    const [show, setShow] = useState(false);
    const navigate = useNavigate();

    const handleClose = () => setShow(false);
    const handleShow = () => setShow(true);
    // a pagination item already exists
    
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
                                    <Col xs={5}>
                                        <Button>Next page</Button>
                                    </Col>
                                    <Col xs={1}>
                                        <Form.Label> 10 </Form.Label>
                                    </Col>
                                    <Col xs={6}>
                                        <Button>Previous page</Button>
                                    </Col>
                                </Row>
                            </Form.Group>
                        </Form>
                    </Col>
                </Row>
                <Row>
                </Row>
            </Container>
        </>
    )
}

export default DashboardView