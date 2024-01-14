import React from "react";
import { useState, useEffect } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable, { tableInit } from '../Table/Table'
import { useFetchCamerasMutation, useAddCamMutation, useUpdateCamMutation, useDeleteCamMutation, camera} from '../../services/camerasService'
import { ITEM_LIST_DISPLAY_CNT } from '../../constants'

const initialCamerasState = {
    headers: ['id', 'Name', 'user', 'source parameters'],
    rows: [],
    detailBtn: false,
    deleteBtn: false,
    editBtn: false,
}

const CamerasListView: React.FC = () => {
    const [getCameras, {isSuccess: cammerasFetched, data: currentCameras}] = useFetchCamerasMutation()
    const [addNewCamera, {isSuccess: successCreatedCam}] = useAddCamMutation()
    const [updateCamera, {isSuccess: successUpdatedCam}] = useUpdateCamMutation()
    const [deleteCamera, {isSuccess: successDeletedCam}] = useDeleteCamMutation()
    const [show, setShow] = useState(false);
    const [selectedEditCamera, setSelectedEditCamera] = useState<camera>();

    const handleClose = () => setShow(false);
    const handleShow = () => setShow(true);


    const [page, setPage] = useState<number>(0)
    const [camerasDisplay, setCamerasDisplay] = useState<tableInit>(initialCamerasState)
    const [newName, setNewName] = useState<string>();
    const handleChangeName = (event: React.ChangeEvent<HTMLInputElement>) => setNewName(event.target.value); //ToDo: perform validations
    const [newParameters, setNewParameters] = useState<string>();
    const handleChangeParameters = (event: React.ChangeEvent<HTMLInputElement>) => setNewParameters(event.target.value); //ToDo: perform validations

    const handleEditCamera  = (cameraId: string) => {
        if (!currentCameras) {
            return
        }
        const selCamera = currentCameras?.find((cameraInfo) => cameraInfo.idVideoSource.toString() === cameraId);
        if (selCamera) {
            setSelectedEditCamera(selCamera);
            setNewName(selCamera.name)
            setNewParameters(selCamera.sourceParameters)
            handleShow();
        } else {
            setShow(false);
        }
    }

    const saveCamera = () => {
        if (!newName || !newParameters || !selectedEditCamera?.idVideoSource) {
            return
        }
        if (selectedEditCamera?.idVideoSource === -1) {
            // create new camera
            addNewCamera({name: newName, sourceParameters: newParameters})
        }
        else {
            // update existing camera data
            updateCamera({name: newName, sourceParameters: newParameters, idVideoSource: selectedEditCamera?.idVideoSource})
        }
    }

    const cleanSelectedCam = () => {
        setSelectedEditCamera({name: "", username: sessionStorage.getItem("user"), sourceParameters:"", idVideoSource: -1} as camera);
    }

    const deleteSelectedCamera = () => {
        if (!selectedEditCamera?.idVideoSource ) {
            return
        }
        if (window.confirm('Quieres elimiar la camara: ' + selectedEditCamera?.name + '?')) {
            deleteCamera({idVideoSource: selectedEditCamera?.idVideoSource});
            setShow(false);
            cleanSelectedCam();
        }
    }

    const fetchCameras = async () => {
        try {
            getCameras({pageCount: page, pageSize: ITEM_LIST_DISPLAY_CNT})
        } catch (error) {
            console.log(error);
        }
    }

    useEffect(() => {
        if (!cammerasFetched || !currentCameras?.length) {
            return
        }
        const newTable = {
            headers: ['Camera id', 'Name', 'User', 'Source parameters'],
            rows: currentCameras.map((camera) => {return [camera.idVideoSource.toString(), camera.name, camera.username, camera.sourceParameters]}),
            detailBtn: false,
            deleteBtn: false,
            editBtn: true,
            editCallback: (selectedNode) => {
                handleEditCamera(selectedNode[0]) 
            }
        } as tableInit
        setCamerasDisplay(newTable)
    }, [cammerasFetched, currentCameras])

    useEffect(() => {
        fetchCameras()
    },[page, successCreatedCam, successUpdatedCam, successDeletedCam])
    
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
                                defaultValue={selectedEditCamera?.idVideoSource}
                                readOnly
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="cameraDetails.name">
                            <Form.Label>camera name</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="cam name ..."
                                defaultValue={selectedEditCamera?.name}
                                onChange={handleChangeName}
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="cameraDetails.name">
                            <Form.Label>user</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="username ..."
                                defaultValue={selectedEditCamera?.username}
                                autoFocus
                                readOnly
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="cameraDetails.path">
                            <Form.Label>Parameters</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="parameters..."
                                defaultValue={selectedEditCamera?.sourceParameters}
                                onChange={handleChangeParameters}
                                autoFocus
                            />
                        </Form.Group>
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={handleClose}>
                        Close
                    </Button>
                    <Button variant="primary" onClick={() => {
                        saveCamera();
                    }}>
                        Save Changes
                    </Button>
                    <Button variant="primary" onClick={deleteSelectedCamera}>
                        Delete
                    </Button>
                </Modal.Footer>
            </Modal>
            <Container >
                <Row className="p-3 mb-2 bg-success bg-gradient text-white rounded-3">
                    <Col xs={2}>
                        <Button onClick={() => {
                            cleanSelectedCam();
                            setShow(true);
                        }}>New Camera</Button>
                    </Col>
                    <Col xs={5} >
                        <Form className="mr-left ">
                            <Form.Group className="mb-3 form-check-inline" controlId="searchFilterField">
                                <Row xs={12}>
                                    <Col xs={2}>
                                        <Form.Label>Filter</Form.Label>
                                    </Col>
                                    <Col xs={5}>
                                        <Form.Control type="text" placeholder="cam name..." />
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