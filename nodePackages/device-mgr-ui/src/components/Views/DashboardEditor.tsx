import React from "react";
import { useState } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable from '../Table/Table'
import { useNavigate } from "react-router-dom"


enum DASHBOARD_EDITOR_VIEW {
    HIDE = 0,
    INIT_DATA,
    LINK_DEVICE,
    SPECIFIC_PARAMETERS
}

const DashboardEditor: React.FC = () => {
    const [dashEditViewState, setDashEditView] = useState(DASHBOARD_EDITOR_VIEW.HIDE);
    const navigate = useNavigate();

    const selectDevice = () => {
        // selecting a device
    }

    const tableContentExample = {
        headers: ["header1", "header2", "header3", "header4"],
        rows: [["1val1", "1val2", "1val3", "1var4"],["2val1", "2val2", "2val3", "2vr4"],["3val1", "3val2", "3val3","3var5"]],
        editBtn: true,
        editCallback: selectDevice
    }
    // a pagination item already exists
    // ToDo: create a multi view modal for edit the current devices
    //       the following is the process for edition or creation
    //       select name/type ----> select asociated device -----> display specific parameters ---> end
    // ToDo: check modal width
    const hideEditor = () => {
        setDashEditView(DASHBOARD_EDITOR_VIEW.HIDE)
    }

    const submitData = () => {
        // add a request here with all the data from the modals
        hideEditor()
    }
    
    return(
        <>
            <Modal show={dashEditViewState == DASHBOARD_EDITOR_VIEW.INIT_DATA} onHide={hideEditor}>
                <Modal.Header closeButton>
                    <Modal.Title>Control - General characteristics</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form>
                        <Form.Group className="mb-3" controlId="controlDetails.name">
                            <Form.Label>control name</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="control name ..."
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
                    <Button variant="primary" onClick={() => { setDashEditView(DASHBOARD_EDITOR_VIEW.LINK_DEVICE) } }>
                        Next
                    </Button>
                    <Button variant="secondary" onClick={hideEditor}>
                        Close
                    </Button>
                </Modal.Footer>
            </Modal>
            <Modal dialogClassName="width: 70%" show={dashEditViewState == DASHBOARD_EDITOR_VIEW.LINK_DEVICE} onHide={hideEditor}>
                <Modal.Header closeButton>
                    <Modal.Title>Control - Link a device</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form>
                        <Form.Group className="mb-3" controlId="controlDetails.name">
                            <Form.Label>select a device</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="selected device id ..."
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="controlDetails.type">
                            <Form.Label>Available devices</Form.Label>
                        </Form.Group>
                    </Form>
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
                                                <Form.Control type="text" placeholder="device name..." />
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
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={() => { setDashEditView(DASHBOARD_EDITOR_VIEW.SPECIFIC_PARAMETERS) }}>
                        Next
                    </Button>
                    <Button variant="secondary" onClick={hideEditor}>
                        Close
                    </Button>
                </Modal.Footer>
            </Modal>
            <Modal show={dashEditViewState == DASHBOARD_EDITOR_VIEW.SPECIFIC_PARAMETERS} onHide={hideEditor}>
                <Modal.Header closeButton>
                    <Modal.Title>Control - Specific characteristics</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={submitData}>
                        Next
                    </Button>
                    <Button variant="secondary" onClick={hideEditor}>
                        Close
                    </Button>
                </Modal.Footer>
            </Modal>
            <Container >
                <Row className="p-3 mb-2 bg-success bg-gradient text-white rounded-3">
                    <Col xs={2}>
                        <Button onClick={ () => { setDashEditView(DASHBOARD_EDITOR_VIEW.INIT_DATA)}}>New element</Button>
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
                    <Col><BaseTable {...tableContentExample}></BaseTable></Col>
                </Row>
            </Container>
        </>
    )
}

export default DashboardEditor