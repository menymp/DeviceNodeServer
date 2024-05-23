import React from "react";
import { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable from '../Table/Table'
import { useNavigate } from "react-router-dom";
import WebSocket from 'ws';
import { dashboardCameraConfigs, useFetchConfigsMutation, useDeleteByIdMutation, useSaveVideoDashboardMutation } from "../../services/camerasDashboardService";
import { ITEM_LIST_DISPLAY_CNT } from '../../constants';

const initialTableState = {
    headers: ['Node id', 'Name', 'Path', 'Protocol', 'Owner', 'Parameters'],
    rows: [],
    detailBtn: false,
    deleteBtn: false,
    editBtn: false,
}

const CamerasDashboardView: React.FC = () => {
    /* implement a editor function to create cameras */
    const [show, setShow] = useState(false);
    const navigate = useNavigate();
    const [getConfigsFetch, {isSuccess: configsLoaded, data: dashConfigs}] = useFetchConfigsMutation();
    const [deleteConfigById, {isSuccess: successDelete }] = useDeleteByIdMutation();
    const [saveDashboardConfig, {isSuccess: successSave }] = useSaveVideoDashboardMutation();

    const [page, setPage] = useState<number>(0);
    const [startVideo, setStartVideo] = useState<boolean>(false);
    const startVideoRef = useRef(false);

    const [selectedConfig, setSelectedConfig] = useState<dashboardCameraConfigs>();
    const currentCameraValues = selectedConfig?.configJsonFetch

    const handleChangeConfig = (event: React.ChangeEvent<HTMLSelectElement>) => {
        if (!configsLoaded || !dashConfigs || !event.target.value) {
            return;
        }
        const selectedConfigTmp = dashConfigs?.find((config) => config.idvideoDashboard === parseInt(event.target.value))
        if (selectedConfigTmp) {
            setSelectedConfig(selectedConfigTmp)
        }
    }

    const handleSaveConfigs = () => {
        if (!selectedConfig) {
            return
        }
        saveDashboardConfig(selectedConfig);
    }

    const handleDeleteConfigs = () => {
        if (!selectedConfig) {
            return
        }
        deleteConfigById(selectedConfig);
    }

    const handleClose = () => setShow(false);
    const handleShow = () => setShow(true);

    const handleNewDashConfig = () => {
        // inits selected data with empty case
        if (!sessionStorage.getItem("userId")) {
            return
        }
        setSelectedConfig({idOwnerUser: parseInt(sessionStorage.getItem("userId")!),idvideoDashboard: -1, configJsonFetch: {height: 400, width: 600, idText: 1, idList: []} });
        handleShow();
    }

    useEffect(() => {
        startVideoRef.current = startVideo;
    }, [startVideo])

    useEffect(() => {
        setSelectedConfig(undefined);
        getConfigsFetch({pageCount: page*ITEM_LIST_DISPLAY_CNT, pageSize: ITEM_LIST_DISPLAY_CNT});
    },[page]);

    useEffect(() => {
        if (!configsLoaded || !dashConfigs || selectedConfig) {
            return;
        }
        setSelectedConfig(dashConfigs[0]);
    }, [configsLoaded, dashConfigs])
    
    const handleStartVideo = () => {
        setStartVideo(true);
        videoLoopStart();
    }

    const handleStopVideo = () => {
        setStartVideo(false);
    }

    const getFrame = () => {
        var image = document.getElementById("videofield");
        if (!image || !selectedConfig) {
            return;
        }
        image.setAttribute('src', "http://localhost:9090/video_feed?vidArgs="+JSON.stringify(selectedConfig.configJsonFetch));
    }

    const videoLoopStart = () => {
        getFrame();
        setTimeout(() => {
            startVideoRef.current && videoLoopStart();
        }, 10);
    }

    const validateAndCreateArray = (input: string): number[] | null => {
        const parts = input.split(',');
    
        // Validate each part
        for (const part of parts) {
            const num = parseInt(part.trim(), 10);
            if (isNaN(num)) {
                // Invalid integer found
                return null;
            }
        }
    
        // Convert valid parts to an array of integers
        const result = parts.map(part => parseInt(part.trim(), 10));
        return result;
    }

    return(
        <>
            <Modal show={show} onHide={handleClose}>
                <Modal.Header closeButton>
                    <Modal.Title>Cameras dashboard</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form>
                        <Form.Group className="mb-3" controlId="deviceParentNode.name">
                            <Form.Label>Height</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="height ..."
                                defaultValue={selectedConfig?.configJsonFetch?.height? currentCameraValues?.height : ""}
                                onChange={(e) => {
                                    if (!selectedConfig) {
                                        return
                                    }
                                    setSelectedConfig({...selectedConfig, configJsonFetch: {...currentCameraValues, height: parseInt(e.target.value)}});
                                }}
                                autoFocus
                            />
                            <Form.Label>Width</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="width ..."
                                defaultValue={currentCameraValues?.width? currentCameraValues?.width : ""}
                                onChange={(e) => {
                                    if (!selectedConfig) {
                                        return
                                    }
                                    setSelectedConfig({...selectedConfig, configJsonFetch: {...currentCameraValues, width: parseInt(e.target.value)}});
                                }}
                            />
                            <Form.Label>Row Length</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="row length ..."
                                defaultValue={currentCameraValues?.rowLen? currentCameraValues?.rowLen : ""}
                                onChange={(e) => {
                                    if (!selectedConfig) {
                                        return
                                    }
                                    setSelectedConfig({...selectedConfig, configJsonFetch: {...currentCameraValues, rowLen: parseInt(e.target.value)}});
                                }}
                            />
                            <Form.Label>Id List</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="id list ..."
                                defaultValue={currentCameraValues?.idList? (currentCameraValues.idList.join(",")) : ""}
                                onChange={(e) => {
                                    const array = validateAndCreateArray(e.target.value);
                                    if (array && selectedConfig) {
                                        setSelectedConfig({...selectedConfig, configJsonFetch: {...currentCameraValues, idList: array}});
                                    }
                                }}
                            />
                            <Form.Label>Id Text</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="id text ..."
                                defaultValue={currentCameraValues?.idText? currentCameraValues?.idText : ""}
                                onChange={(e) => {
                                    if (!selectedConfig) {
                                        return
                                    }
                                    setSelectedConfig({...selectedConfig, configJsonFetch: {...currentCameraValues, idText: parseInt(e.target.value)}});
                                }}
                            />
                        </Form.Group>
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={() =>{
                            handleSaveConfigs();
                            handleClose();
                        }}>
                        Save
                    </Button>
                    <Button variant="secondary" onClick={() =>{
                            handleDeleteConfigs();
                            handleClose();
                        }}>
                        Delete
                    </Button>
                    <Button variant="secondary" onClick={() =>{
                            handleClose();
                        }}>
                        Close
                    </Button>
                </Modal.Footer>
            </Modal>
            <Container >
                <Row className="p-3 mb-2 bg-success bg-gradient text-white rounded-3">
                    <Col xs={2}>
                        <Button onClick={handleShow}>Editor</Button>
                    </Col>
                    <Col xs={2}>
                        <Button onClick={handleStartVideo}>Start</Button>
                    </Col>
                    <Col xs={2}>
                        <Button onClick={handleStopVideo}>Stop</Button>
                    </Col>
                    <Col xs={2}>
                        <Button onClick={handleNewDashConfig}>New config...</Button>
                    </Col>
                    <Col xs={2}>
                        <Form.Group className="mb-3" controlId="nodeDetails.protocol">
                            <Form.Label>Node protocol</Form.Label>
                            <Form.Select onChange={handleChangeConfig} aria-label="MQTT" id="selectedConfigItem">
                                {dashConfigs?.map((value, index) => { return <option id={`${index}`} value={value.idvideoDashboard}>{value.idvideoDashboard}</option>})}
                            </Form.Select>
                        </Form.Group>
                    </Col>
                    <Col>
                        <Form className="mr-left ">
                            <Form.Group className="mb-3 form-check-inline" controlId="searchFilterField">
                                <Row xs={12}>
                                    <Col xs={5}>
                                        <Button onClick={() => {(page > 0) && setPage(page - 1)}}>Previous page</Button>
                                    </Col>
                                    <Col xs={1}>
                                        <Form.Label>{page}</Form.Label>
                                    </Col>
                                    <Col xs={6}>
                                        <Button onClick={() => {setPage(page + 1)}}>Next page</Button>
                                    </Col>
                                </Row>
                            </Form.Group>
                        </Form>
                    </Col>
                </Row>
                <Row>
                    <img id="videofield" />
                </Row>
            </Container>
        </>
    )
}

export default CamerasDashboardView