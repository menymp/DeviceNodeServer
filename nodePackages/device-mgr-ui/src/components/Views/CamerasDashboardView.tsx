import React from "react";
import { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import {
    useFetchDashboardsQuery,
    useCreateDashboardMutation,
    useUpdateDashboardMutation,
    useDeleteDashboardMutation,
    VideoDashboard,
    ConfigCameraData,
} from "../../services/camerasDashboardService";
import { ITEM_LIST_DISPLAY_CNT } from '../../constants';

const CamerasDashboardView: React.FC = () => {
    const { data: dashConfigs = [], isSuccess: configsLoaded, refetch } = useFetchDashboardsQuery();
    const [createDashboard] = useCreateDashboardMutation();
    const [updateDashboard] = useUpdateDashboardMutation();
    const [deleteDashboard] = useDeleteDashboardMutation();

    const [show, setShow] = useState(false);
    const [page, setPage] = useState<number>(0);
    const [startVideo, setStartVideo] = useState<boolean>(false);
    const startVideoRef = useRef(false);
    const [selectedConfig, setSelectedConfig] = useState<VideoDashboard | undefined>();

    const currentCameraValues: ConfigCameraData = selectedConfig?.config ?? {};

    const handleChangeConfig = (event: React.ChangeEvent<HTMLSelectElement>) => {
        if (!configsLoaded || !dashConfigs || !event.target.value) {
            return;
        }
        const selectedConfigTmp = dashConfigs.find((config) => config.id === parseInt(event.target.value, 10));
        if (selectedConfigTmp) {
            setSelectedConfig(selectedConfigTmp);
        }
    }

    const handleSaveConfigs = async () => {
        if (!selectedConfig || !selectedConfig.config) {
            return;
        }

        if (selectedConfig.id === -1) {
            await createDashboard({ configJsonFetch: selectedConfig.config });
        } else {
            await updateDashboard({ id: selectedConfig.id, configJsonFetch: selectedConfig.config });
        }

        refetch();
    }

    const handleDeleteConfigs = async () => {
        if (!selectedConfig || selectedConfig.id === -1) {
            return;
        }
        if (window.confirm('Quieres elimiar la configuracion: ' + selectedConfig.id + '?')) {
            await deleteDashboard({ id: selectedConfig.id });
            refetch();
            setShow(false);
        }
    }

    const handleClose = () => {
        refetch();
        setShow(false);
    }

    const handleShow = () => {
        setShow(true);
    }

    const handleNewDashConfig = () => {
        const userId = sessionStorage.getItem("userId");
        if (!userId) {
            return;
        }
        setSelectedConfig({
            id: -1,
            config: { height: 400, width: 600, idText: 1, idList: [], rowLen: 0 },
            idOwnerUser: parseInt(userId, 10),
        });
        handleShow();
    }

    useEffect(() => {
        startVideoRef.current = startVideo;
    }, [startVideo]);

    useEffect(() => {
        setSelectedConfig(undefined);
        refetch();
    }, [page, refetch]);

    useEffect(() => {
        if (!dashConfigs || dashConfigs.length === 0 || selectedConfig) {
            return;
        }
        setSelectedConfig(dashConfigs[0]);
    }, [dashConfigs, selectedConfig]);

    const handleStartVideo = () => {
        setStartVideo(true);
        videoLoopStart();
    }

    const handleStopVideo = () => {
        setStartVideo(false);
    }

    const getFrame = () => {
        const image = document.getElementById("videofield");
        if (!image || !selectedConfig || !selectedConfig.config) {
            return;
        }
        image.setAttribute('src', `${process.env.REACT_APP_VIDEO_SEED_URL}${JSON.stringify(JSON.stringify(selectedConfig.config))}`);
    }

    const videoLoopStart = () => {
        getFrame();
        setTimeout(() => {
            startVideoRef.current && videoLoopStart();
        }, 10);
    }

    const validateAndCreateArray = (input: string): number[] | null => {
        const parts = input.split(',');

        for (const part of parts) {
            const num = parseInt(part.trim(), 10);
            if (isNaN(num)) {
                return null;
            }
        }

        return parts.map(part => parseInt(part.trim(), 10));
    }

    return (
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
                                defaultValue={currentCameraValues.height ?? ""}
                                onChange={(e) => {
                                    if (!selectedConfig) {
                                        return;
                                    }
                                    setSelectedConfig({
                                        ...selectedConfig,
                                        config: { ...currentCameraValues, height: parseInt(e.target.value, 10) },
                                    });
                                }}
                                autoFocus
                            />
                            <Form.Label>Width</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="width ..."
                                defaultValue={currentCameraValues.width ?? ""}
                                onChange={(e) => {
                                    if (!selectedConfig) {
                                        return;
                                    }
                                    setSelectedConfig({
                                        ...selectedConfig,
                                        config: { ...currentCameraValues, width: parseInt(e.target.value, 10) },
                                    });
                                }}
                            />
                            <Form.Label>Row Length</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="row length ..."
                                defaultValue={currentCameraValues.rowLen ?? ""}
                                onChange={(e) => {
                                    if (!selectedConfig) {
                                        return;
                                    }
                                    setSelectedConfig({
                                        ...selectedConfig,
                                        config: { ...currentCameraValues, rowLen: parseInt(e.target.value, 10) },
                                    });
                                }}
                            />
                            <Form.Label>Id List</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="id list ..."
                                defaultValue={currentCameraValues.idList ? currentCameraValues.idList.join(",") : ""}
                                onChange={(e) => {
                                    const array = validateAndCreateArray(e.target.value);
                                    if (array && selectedConfig) {
                                        setSelectedConfig({
                                            ...selectedConfig,
                                            config: { ...currentCameraValues, idList: array },
                                        });
                                    }
                                }}
                            />
                            <Form.Label>Id Text</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="id text ..."
                                defaultValue={currentCameraValues.idText ?? ""}
                                onChange={(e) => {
                                    if (!selectedConfig) {
                                        return;
                                    }
                                    setSelectedConfig({
                                        ...selectedConfig,
                                        config: { ...currentCameraValues, idText: parseInt(e.target.value, 10) },
                                    });
                                }}
                            />
                        </Form.Group>
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button
                        variant="primary"
                        onClick={() => {
                            handleSaveConfigs();
                            handleClose();
                        }}
                    >
                        Save
                    </Button>
                    <Button
                        variant="secondary"
                        onClick={() => {
                            handleDeleteConfigs();
                            handleClose();
                        }}
                    >
                        Delete
                    </Button>
                    <Button variant="secondary" onClick={handleClose}>
                        Close
                    </Button>
                </Modal.Footer>
            </Modal>
            <Container>
                <Row className="p-3 mb-2 bg-success bg-gradient text-white rounded-3">
                    <Col xs={1}>
                        <Button onClick={handleShow}>Editor</Button>
                    </Col>
                    <Col xs={1}>
                        <Button onClick={handleStartVideo}>Start</Button>
                    </Col>
                    <Col xs={1}>
                        <Button onClick={handleStopVideo}>Stop</Button>
                    </Col>
                    <Col xs={2}>
                        <Button onClick={handleNewDashConfig}>New config...</Button>
                    </Col>
                    <Col xs={2}>
                        <Form.Group className="mb-3" controlId="nodeDetails.protocol">
                            <Form.Label>Node protocol</Form.Label>
                            <Form.Select onChange={handleChangeConfig} aria-label="MQTT" id="selectedConfigItem">
                                {dashConfigs.map((value, index) => (
                                    <option key={value.id} id={`${index}`} value={value.id}>
                                        {value.id}
                                    </option>
                                ))}
                            </Form.Select>
                        </Form.Group>
                    </Col>
                    <Col>
                        <Form className="mr-left ">
                            <Form.Group className="mb-3 form-check-inline" controlId="searchFilterField">
                                <Row xs={12}>
                                    <Col xs={5}>
                                        <Button onClick={() => page > 0 && setPage(page - 1)}>Previous page</Button>
                                    </Col>
                                    <Col xs={1}>
                                        <Form.Label>{page}</Form.Label>
                                    </Col>
                                    <Col xs={6}>
                                        <Button onClick={() => setPage(page + 1)}>Next page</Button>
                                    </Col>
                                </Row>
                            </Form.Group>
                        </Form>
                    </Col>
                </Row>
                <Row>
                    <img id="videofield" alt="Video dashboard" />
                </Row>
            </Container>
        </>
    );
};

export default CamerasDashboardView;