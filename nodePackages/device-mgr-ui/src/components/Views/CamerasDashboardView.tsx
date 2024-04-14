import React from "react";
import { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable from '../Table/Table'
import { useNavigate } from "react-router-dom";
import WebSocket from 'ws';
import { dashboardCameraConfigs, useFetchConfigsMutation } from "../../services/camerasDashboardService";
import { ITEM_LIST_DISPLAY_CNT } from '../../constants';

const initialTableState = {
    headers: ['Node id', 'Name', 'Path', 'Protocol', 'Owner', 'Parameters'],
    rows: [],
    detailBtn: false,
    deleteBtn: false,
    editBtn: false,
}

const CamerasDashboardView: React.FC = () => {
    const [show, setShow] = useState(false);
    const navigate = useNavigate();
    const [getConfigsFetch, {isSuccess: configsLoaded, data: dashConfigs}] = useFetchConfigsMutation();
    const [page, setPage] = useState<number>(0);
    const [startVideo, setStartVideo] = useState<boolean>(false);
    const startVideoRef = useRef(false);

    const [selectedConfig, setSelectedConfig] = useState<dashboardCameraConfigs>();
    const handleChangeConfig = (event: React.ChangeEvent<HTMLSelectElement>) => {
        if (!configsLoaded || !dashConfigs || !event.target.value) {
            return;
        }
        const selectedConfigTmp = dashConfigs?.find((config) => config.idvideoDashboard === parseInt(event.target.value))
        if (selectedConfigTmp) {
            setSelectedConfig(selectedConfigTmp)
        }
    }

    const handleClose = () => setShow(false);
    const handleShow = () => setShow(true);

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
                                autoFocus
                            />
                            <Form.Label>Width</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="width ..."
                                autoFocus
                            />
                            <Form.Label>Row Length</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="row length ..."
                                autoFocus
                            />
                        </Form.Group>
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={handleClose}>
                        Save
                    </Button>
                    <Button variant="secondary" onClick={handleClose}>
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