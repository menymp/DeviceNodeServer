import React from "react";
import { useState } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable from '../Table/Table'


const NodesListView: React.FC = () => {
    const [show, setShow] = useState(false);

    const handleClose = () => setShow(false);
    const handleShow = () => setShow(true);

    const tableContentExample = {
        headers: ["header1", "header2", "header3"],
        rows: ["val1", "val2", "val3"],
        detailBtn: true,
        detailCallback: handleShow,
        deleteBtn: true,
        editBtn: true
    }
    // a pagination item already exists
    
    return(
        <>
            <Modal show={show} onHide={handleClose}>
                <Modal.Header closeButton>
                    <Modal.Title>Node details</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form>
                        <Form.Group className="mb-3" controlId="nodeDetails.name">
                            <Form.Label>Node name</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="node name ..."
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="nodeDetails.path">
                            <Form.Label>Node path</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="/nodePath/..."
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="nodeDetails.protocol">
                            <Form.Label>Node protocol</Form.Label>
                            <Form.Select aria-label="MQTT">
                                <option value="1">MQTT</option>
                                <option value="2">SOCKET</option>
                            </Form.Select>
                        </Form.Group>
                        <Form.Group
                            className="mb-3"
                            controlId="nodeDetails.parameters"
                            >
                            <Form.Label>Parameters</Form.Label>
                            <Form.Control as="textarea" rows={3} />
                        </Form.Group>
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={handleClose}>
                        Close
                    </Button>
                    <Button variant="primary" onClick={handleClose}>
                        Save Changes
                    </Button>
                    <Button variant="primary" onClick={handleClose}>
                        Delete
                    </Button>
                </Modal.Footer>
            </Modal>
            <Container >
                <Row>
                    <Col xs={2}>
                        <Button>New Node</Button>
                    </Col>
                    <Col xs={5} >
                        <Form className="mr-left ">
                            <Form.Group className="mb-3 form-check-inline" controlId="searchFilterField">
                                <Row xs={12}>
                                    <Col xs={4}>
                                        <Form.Select aria-label="Default select example">
                                            <option value="1">Name</option>
                                            <option value="2">Type</option>
                                            <option value="3">Path</option>
                                        </Form.Select>
                                    </Col>
                                    <Col xs={2}>
                                        <Form.Label>Name</Form.Label>
                                    </Col>
                                    <Col xs={5}>
                                        <Form.Control type="text" placeholder="node name..." />
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
                    <Col><BaseTable {...tableContentExample}></BaseTable></Col>
                </Row>
            </Container>
        </>
    )
}

export default NodesListView