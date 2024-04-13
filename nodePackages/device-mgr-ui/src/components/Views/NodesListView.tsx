import React from "react";
import { useState, useEffect } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable, { tableInit } from '../Table/Table'
import { useFetchNodesMutation, node, useFetchProtocolsMutation, protocolInfo, useSaveNodeMutation, useDeleteNodeMutation, useCreateNodeMutation } from '../../services/nodesService'
import { ITEM_LIST_DISPLAY_CNT } from '../../constants'

const initialTableState = {
    headers: ['Node id', 'Name', 'Path', 'Protocol', 'Owner', 'Parameters'],
    rows: [],
    detailBtn: false,
    deleteBtn: false,
    editBtn: false,
}

const NodesListView: React.FC = () => {
    
    const [getNodes, {isSuccess: nodesLoaded, data: nodesData}] = useFetchNodesMutation();
    const [getProtocols, {isSuccess: protocolsLoaded, data: protocolData}] = useFetchProtocolsMutation();
    const [updateNodeInfo, {isSuccess: updatedNodeInfo}] = useSaveNodeMutation();
    const [deleteNode, {isSuccess: deletedNode}] = useDeleteNodeMutation();
    const [createNode, {isSuccess: createNodeSuccess}] = useCreateNodeMutation();
    const [protocols, setProtocols] = useState<Array<protocolInfo>>([]);
    const [selectedEditNode, setSelectedEditNode] = useState<node>();
    const [show, setShow] = useState(false);
    const [page, setPage] = useState<number>(0);
    const [nodesDisplay, setNodesDisplay] = useState<tableInit>(initialTableState);

    const [newName, setNewName] = useState<string>();
    const handleChangeName = (event: React.ChangeEvent<HTMLInputElement>) => setNewName(event.target.value); //ToDo: perform validations
    const [newPath, setNewPath] = useState<string>();
    const handleChangePath = (event: React.ChangeEvent<HTMLInputElement>) => setNewPath(event.target.value); //ToDo: perform validations
    const [newProtocol, setNewProtocol] = useState<number>();
    const handleChangeProtocol = (event: React.ChangeEvent<HTMLSelectElement>) => setNewProtocol(parseInt(event.target.value)); //ToDo: perform validations
    const [newParameters, setNewParameters] = useState<string>();
    const handleChangeParameters = (event: React.ChangeEvent<HTMLInputElement>) => setNewParameters(event.target.value); //ToDo: perform validations

    const handleClose = () => {
        setShow(false)
    };

    const handleEditNode = (nodeId: string) => {
        const selectedEditNode = nodesData?.find((nodeObj) => nodeObj.idNodesTable.toString() === nodeId)
        if (selectedEditNode) {
            setSelectedEditNode(selectedEditNode)
            setNewName(selectedEditNode?.nodeName)
            setNewPath(selectedEditNode?.nodePath)
            setNewParameters(selectedEditNode?.connectionParameters)
            setNewProtocol(selectedEditNode?.idDeviceProtocol)
            setShow(true)
        }
        else
        {
            setShow(false)
        }
    };

    const saveElement = () => {
        let selectedProtocol = "";
        let tmp = getCurrentProtocolSelection();

        if (tmp) {
            selectedProtocol = tmp // ToDo check this!!!!
        } else {
            selectedProtocol = newProtocol?.toString()!
        }
        if (!newName || !newPath || !selectedProtocol || !newParameters) {
            return
        }
        if (selectedEditNode?.idNodesTable == -1) {
            createNode({nodeName: newName, 
                nodePath: newPath, 
                nodeProtocol: selectedProtocol.toString(), 
                nodeParameters: newParameters,
            });
        } else {
            updateNodeInfo({nodeName: newName, 
                nodePath: newPath, 
                nodeProtocol: selectedProtocol.toString(), 
                nodeParameters: newParameters,
            });
        }
        setShow(false);
        cleanSelectedNode();
        getNodes({pageCount: page, pageSize: ITEM_LIST_DISPLAY_CNT})
        getProtocols();
    }

    const deleteElement = () => {
        if (!selectedEditNode?.nodeName) {
            return
        }
        if (window.confirm('Quieres elimiar el nodo: ' + selectedEditNode?.nodeName + '?')) {
            deleteNode({nodeName: selectedEditNode?.nodeName});
            setShow(false);
            cleanSelectedNode();
            getNodes({pageCount: page, pageSize: ITEM_LIST_DISPLAY_CNT})
            getProtocols();
        }

    }

    const cleanSelectedNode = () => {
        setSelectedEditNode({nodeName: "", idDeviceProtocol: 0, nodePath: "", connectionParameters:"", idNodesTable: -1} as node);
    }

    useEffect(() => {
        getNodes({pageCount: page, pageSize: ITEM_LIST_DISPLAY_CNT})
        getProtocols();
    },[page]);

    useEffect(() => {
        if (!protocolsLoaded || !protocolData || !protocolData?.length) {
            return
        }
        setProtocols(protocolData)
    }, [protocolsLoaded ,protocolData])

    useEffect(() => {
        if (!nodesLoaded || !nodesData || !nodesData.length) {
            setNodesDisplay(initialTableState);
            return
        }
        const newTable = {
            headers: ['Node id', 'Name', 'Path', 'Protocol', 'Owner', 'Parameters'],
            rows: nodesData.map((node) => {return [node.idNodesTable.toString(), node.nodeName, node.nodePath, node.idDeviceProtocol.toString(), node.idOwnerUser.toString(), node.connectionParameters.toString()]}),
            detailBtn: false,
            deleteBtn: false,
            editBtn: true,
            editCallback: (selectedNode) => {
                handleEditNode(selectedNode[0]) 
            }
        } as tableInit
        setNodesDisplay(newTable);
    }, [nodesLoaded, nodesData])
    //ToDo: we can not change the node name once created, should it be selected instead by id??????
    const getCurrentProtocolSelection = () => {
        const value = (document.getElementById('selectedProtocolItem') as HTMLSelectElement).value;
        return value;
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
                                defaultValue={selectedEditNode?.nodeName}
                                onChange={handleChangeName}
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="nodeDetails.path">
                            <Form.Label>Node path</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="/nodePath/..."
                                defaultValue={selectedEditNode?.nodePath}
                                onChange={handleChangePath}
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="nodeDetails.protocol">
                            <Form.Label>Node protocol</Form.Label>
                            <Form.Select onChange={handleChangeProtocol} aria-label="MQTT" id="selectedProtocolItem">
                                {protocols?.map((value, index) => { return <option id={`${index}`} value={value.idsupportedProtocols}>{value.ProtocolName}</option>})}
                            </Form.Select>
                        </Form.Group>
                        <Form.Group
                            className="mb-3"
                            controlId="nodeDetails.parameters"
                            >
                            <Form.Label>Parameters</Form.Label>
                            <Form.Control as="textarea" rows={3} 
                                onChange={handleChangeParameters} 
                                placeholder='{"node":"parameters"}...' 
                                defaultValue={selectedEditNode?.connectionParameters} 
                            />
                        </Form.Group>
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={handleClose}>
                        Close
                    </Button>
                    <Button variant="primary" onClick={() => {

                        saveElement();
                    }}>
                        Save Changes
                    </Button>
                    <Button variant="primary" onClick={deleteElement}>
                        Delete
                    </Button>
                </Modal.Footer>
            </Modal>
            <Container >
                <Row className="p-3 mb-2 bg-success bg-gradient text-white rounded-3">
                    <Col xs={2}>
                        <Button onClick={() => {
                            cleanSelectedNode();
                            setShow(true);
                        }}>New Node</Button>
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
                                    <Col xs={6}>
                                        <Button onClick={() => {(page > 0) && setPage(page - 1)}}>Previous page</Button>
                                    </Col>
                                    <Col xs={1}>
                                        <Form.Label>{page}</Form.Label>
                                    </Col>
                                    <Col xs={5}>
                                        <Button onClick={() => {setPage(page + 1)}}>Next page</Button>
                                    </Col>
                                </Row>
                            </Form.Group>
                        </Form>
                    </Col>
                </Row>
                <Row>
                    <Col><BaseTable {...nodesDisplay}></BaseTable></Col>
                </Row>
            </Container>
        </>
    )
}

export default NodesListView