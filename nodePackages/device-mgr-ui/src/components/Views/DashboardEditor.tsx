import React from "react";
import { useEffect, useState } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable, { tableInit } from '../Table/Table'
import { useNavigate } from "react-router-dom"
import { useFetchControlsMutation, Control } from "../../services/dashboardService";
import { ITEM_LIST_DISPLAY_CNT } from "../../constants";


enum DASHBOARD_EDITOR_VIEW {
    HIDE = 0,
    INIT_DATA,
    LINK_DEVICE,
    SPECIFIC_PARAMETERS
}

const initialTableState = {
    headers: ['id', 'name', 'parameters', 'type'],
    rows: [],
    detailBtn: false,
    deleteBtn: false,
    editBtn: false,
}

const DashboardEditor: React.FC = () => {
    const [dashEditViewState, setDashEditView] = useState(DASHBOARD_EDITOR_VIEW.HIDE);
    const [getControls, {isSuccess: controlsLoaded, data: controls}] = useFetchControlsMutation();

    const navigate = useNavigate();
    const [page, setPage] = useState<number>(0);
    const [displayControls, setDisplayControls] = useState<tableInit>(initialTableState);
    const [selectedEditControl, setSelectedEditControl] = useState<Control>();

    const selectDevice = () => {
        // selecting a device
    }

    useEffect(() => {
        if (!controlsLoaded || !controls.length) {
            setDisplayControls(initialTableState);
            return
        }
        //set ui fetched controls
        const newTable = {
            headers: ['id', 'name', 'parameters', 'type'],
            rows: controls.map((control) => {return [control.idControl.toString(), control.name, control.parameters, control.typename]}),
            detailBtn: false,
            deleteBtn: false,
            editBtn: true,
            editCallback: (selectedControl) => {
                handleEditControl(selectedControl[0]) 
            }
        } as tableInit
        setDisplayControls(newTable);
    }, [controlsLoaded, controls])

    const handleEditControl = (idSelectControl: string) => {
        const selectedEditControl = controls?.find((controlObj) => controlObj.idControl.toString() === idSelectControl)
        if (selectedEditControl) {
            setSelectedEditControl(selectedEditControl)
            // setShow(true)
        }
        else
        {
            // setShow(false)
        }
    }

    useEffect(() => {
        getControls({pageCount: page, pageSize: ITEM_LIST_DISPLAY_CNT})
    },[page]);
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
                                defaultValue={selectedEditControl?.name}
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
                            <Form.Label>select a link</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="selected control ..."
                                defaultValue={selectedEditControl?.idControl}
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
                            <Col><BaseTable {...displayControls}></BaseTable></Col>
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
                <Form>
                    <Form.Group className="mb-3" controlId="controlDetails.name">
                        <Form.Label>control name</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="control name ..."
                                defaultValue={selectedEditControl?.idControl}
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
                    <Col><BaseTable {...displayControls}></BaseTable></Col>
                </Row>
            </Container>
        </>
    )
}

export default DashboardEditor