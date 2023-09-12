import React from "react";
import { useState } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable from '../Table/Table'
import { useNavigate } from "react-router-dom"


const DashboardEditor: React.FC = () => {
    const [showModalEdit1, setShowEdit1] = useState(false);
    const navigate = useNavigate();

    const handleEdit1 = () => setShowEdit1(false);
    // a pagination item already exists
    // ToDo: create a multi view modal for edit the current devices
    //       the following is the process for edition or creation
    //       select name/type ----> select asociated device -----> display specific parameters ---> end
    
    return(
        <>
            <Modal show={showModalEdit1} onHide={handleEdit1}>
                <Modal.Header closeButton>
                    <Modal.Title>Dashboard control</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form>
                        <Form.Group className="mb-3" controlId="controlDetails.name">
                            <Form.Label>device name</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="node name ..."
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="controlDetails.type">
                            <Form.Label>device id</Form.Label>
                            <Form.Select aria-label="select type">
                                            <option value="1">control1</option>
                                            <option value="2">control2</option>
                                            <option value="3">control3</option>
                            </Form.Select>
                        </Form.Group>
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={handleClose}>
                        Next
                    </Button>
                    <Button variant="secondary" onClick={handleClose}>
                        Close
                    </Button>
                </Modal.Footer>
            </Modal>
            <Modal show={show} onHide={handleClose}>
                <Modal.Header closeButton>
                    <Modal.Title>Dashboard control</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form>
                        <Form.Group className="mb-3" controlId="controlDetails.name">
                            <Form.Label>device name</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="node name ..."
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="controlDetails.type">
                            <Form.Label>device id</Form.Label>
                            <Form.Select aria-label="select type">
                                            <option value="1">control1</option>
                                            <option value="2">control2</option>
                                            <option value="3">control3</option>
                            </Form.Select>
                        </Form.Group>
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={handleClose}>
                        Next
                    </Button>
                    <Button variant="secondary" onClick={handleClose}>
                        Close
                    </Button>
                </Modal.Footer>
            </Modal>
            <Container >
                <Row className="p-3 mb-2 bg-success bg-gradient text-white rounded-3">
                    <Col xs={2}>
                        <Button onClick={handleShow}>New element</Button>
                    </Col>
                    <Col xs={2}>
                        <Button onClick={() => { navigate('/Dashboard') }}>Dashboard view</Button>
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

export default DashboardEditor