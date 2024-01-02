import React from "react";
import { useState, useEffect } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable, { tableInit } from '../Table/Table'
import { useFetchNodesMutation, node } from '../../services/nodesService'
import { ITEM_LIST_DISPLAY_CNT } from '../../constants'



const NodesListView: React.FC = () => {
    const [show, setShow] = useState(false);
    const [getNodes] = useFetchNodesMutation()
    const [nodes, setNodes] = useState<Array<node>>()
    const [selectedEditNode, setSelectedEditNode] = useState<node>()

    const handleClose = () => setShow(false);
    const handleEditNode = (nodeId: string) => {
        const selectedEditNode = nodes?.find((nodeObj) => nodeObj.idNodesTable.toString() === nodeId)
        if (selectedEditNode) {
            setSelectedEditNode(selectedEditNode)
            setShow(true)
        }
        else
        {
            setShow(false)
        }
    };

    const tableContentExample = {
        headers: ["header1", "header2", "header3", "header4"],
        rows: [["1val1", "1val2", "1val3", "1var4"],["2val1", "2val2", "2val3", "2vr4"],["3val1", "3val2", "3val3","3var5"]],
        detailBtn: false,
        deleteBtn: true,
        editBtn: true
    }

    const [page, setPage] = useState<number>(0)
    const [nodesDisplay, setNodesDisplay] = useState<tableInit>(tableContentExample)

    const fetchNodes = async () => {
        try {
            const nodes = await getNodes({pageCount: page, pageSize: ITEM_LIST_DISPLAY_CNT}).unwrap()
            setNodes(nodes)
            const newTable = {
                headers: ['Node id', 'Name', 'Path', 'Protocol', 'Owner', 'Parameters'],
                rows: nodes.map((node) => {return [node.idNodesTable.toString(), node.nodeName, node.nodePath, node.idDeviceProtocol.toString(), node.idOwnerUser.toString(), node.connectionParameters.toString()]}),
                detailBtn: false,
                deleteBtn: true,
                editBtn: true,
                editCallback: (selectedNode) => { 
                    alert("edit" + " " + selectedNode[0])
                    handleEditNode(selectedNode[0]) 
                }
            } as tableInit
            setNodesDisplay(newTable)
        } catch (error) {
            console.log(error);
        }
    }

    useEffect(() => {
        fetchNodes()
    },[page])

    useEffect(() => {

    }, [nodesDisplay])
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
                                value={selectedEditNode?.nodeName}
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="nodeDetails.path">
                            <Form.Label>Node path</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="/nodePath/..."
                                value={selectedEditNode?.nodePath}
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
                <Row className="p-3 mb-2 bg-success bg-gradient text-white rounded-3">
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
                    <Col><BaseTable {...nodesDisplay}></BaseTable></Col>
                </Row>
            </Container>
        </>
    )
}

export default NodesListView