import React, { useMemo, useState } from "react";
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable, { tableInit } from '../Table/Table';
import { useFetchNodesQuery, useFetchProtocolsQuery, Node, ProtocolInfo } from '../../services/nodesService';
import { ITEM_LIST_DISPLAY_CNT } from '../../constants';

const initialTableState = {
    headers: ['Node id', 'Name', 'Path', 'Protocol', 'Owner', 'Parameters'],
    rows: [],
    detailBtn: false,
    deleteBtn: false,
    editBtn: false,
} as tableInit;

const NodesListView: React.FC = () => {
    const [page, setPage] = useState<number>(0);
    const [filterField, setFilterField] = useState<'name' | 'path' | 'protocol' | 'owner'>('name');
    const [filterValue, setFilterValue] = useState<string>('');
    const [selectedNode, setSelectedNode] = useState<Node | null>(null);
    const [showDetails, setShowDetails] = useState(false);

    const {
        data: nodesData,
        isLoading: nodesLoading,
        isError: nodesError,
        refetch: refetchNodes,
    } = useFetchNodesQuery({ page, size: ITEM_LIST_DISPLAY_CNT });

    const {
        data: protocolData,
        isLoading: protocolsLoading,
        isError: protocolsError,
    } = useFetchProtocolsQuery();

    const protocolById = useMemo<Record<number, string>>(() => {
        return (protocolData ?? []).reduce<Record<number, string>>((map: Record<number, string>, protocol: ProtocolInfo) => {
            map[protocol.idsupportedProtocols] = protocol.ProtocolName;
            return map;
        }, {});
    }, [protocolData]);

    const filteredNodes = useMemo<Node[]>(() => {
        if (!nodesData || !filterValue.trim()) {
            return nodesData ?? [];
        }

        const normalizedFilter = filterValue.trim().toLowerCase();
        return (nodesData ?? []).filter((node: Node) => {
            switch (filterField) {
                case 'path':
                    return node.nodePath?.toLowerCase().includes(normalizedFilter);
                case 'protocol':
                    return (protocolById[node.idDeviceProtocol] ?? node.idDeviceProtocol.toString()).toLowerCase().includes(normalizedFilter);
                case 'owner':
                    return node.idOwnerUser.toString().includes(normalizedFilter);
                default:
                    return node.nodeName?.toLowerCase().includes(normalizedFilter);
            }
        });
    }, [nodesData, filterField, filterValue, protocolById]);

    const nodesDisplay = useMemo<tableInit>(() => {
        return {
            headers: ['Node id', 'Name', 'Path', 'Protocol', 'Owner', 'Parameters'],
            rows: filteredNodes.map((node: Node) => [
                node.idNodesTable.toString(),
                node.nodeName ?? '',
                node.nodePath ?? '',
                protocolById[node.idDeviceProtocol] ?? node.idDeviceProtocol.toString(),
                node.idOwnerUser.toString(),
                node.connectionParameters != null
                    ? typeof node.connectionParameters === 'string'
                        ? node.connectionParameters
                        : JSON.stringify(node.connectionParameters)
                    : '',
            ]),
            detailBtn: true,
            deleteBtn: false,
            editBtn: false,
            detailCallback: (selectedRow) => {
                const id = parseInt(selectedRow[0], 10);
                const node = nodesData?.find((item: Node) => item.idNodesTable === id) ?? null;
                setSelectedNode(node);
                setShowDetails(true);
            },
        } as tableInit;
    }, [filteredNodes, protocolById, nodesData]);

    const handleCloseDetails = () => setShowDetails(false);

    const handleFilterFieldChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        setFilterField(event.target.value as 'name' | 'path' | 'protocol' | 'owner');
    };

    const handleFilterValueChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setFilterValue(event.target.value);
    };

    const handleRefresh = () => {
        refetchNodes();
    };

    const protocolLabel = (protocolId: number) => protocolById[protocolId] ?? protocolId.toString();

    return (
        <>
            <Modal show={showDetails} onHide={handleCloseDetails}>
                <Modal.Header closeButton>
                    <Modal.Title>Node details</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {selectedNode ? (
                        <Form>
                            <Form.Group className="mb-3" controlId="nodeDetails.id">
                                <Form.Label>Node id</Form.Label>
                                <Form.Control type="text" readOnly defaultValue={selectedNode.idNodesTable} />
                            </Form.Group>
                            <Form.Group className="mb-3" controlId="nodeDetails.name">
                                <Form.Label>Node name</Form.Label>
                                <Form.Control type="text" readOnly defaultValue={selectedNode.nodeName} />
                            </Form.Group>
                            <Form.Group className="mb-3" controlId="nodeDetails.path">
                                <Form.Label>Node path</Form.Label>
                                <Form.Control type="text" readOnly defaultValue={selectedNode.nodePath} />
                            </Form.Group>
                            <Form.Group className="mb-3" controlId="nodeDetails.protocol">
                                <Form.Label>Protocol</Form.Label>
                                <Form.Control type="text" readOnly defaultValue={protocolLabel(selectedNode.idDeviceProtocol)} />
                            </Form.Group>
                            <Form.Group className="mb-3" controlId="nodeDetails.owner">
                                <Form.Label>Owner</Form.Label>
                                <Form.Control type="text" readOnly defaultValue={selectedNode.idOwnerUser.toString()} />
                            </Form.Group>
                            <Form.Group className="mb-3" controlId="nodeDetails.parameters">
                                <Form.Label>Parameters</Form.Label>
                                <Form.Control
                                    as="textarea"
                                    rows={5}
                                    readOnly
                                    value={
                                        selectedNode.connectionParameters != null
                                            ? typeof selectedNode.connectionParameters === 'string'
                                                ? selectedNode.connectionParameters
                                                : JSON.stringify(selectedNode.connectionParameters, null, 2)
                                            : ''
                                    }
                                />
                            </Form.Group>
                        </Form>
                    ) : (
                        <div>No node selected.</div>
                    )}
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={handleCloseDetails}>
                        Close
                    </Button>
                </Modal.Footer>
            </Modal>

            <Container>
                <Row className="p-3 mb-2 bg-success bg-gradient text-white rounded-3">
                    <Col xs={12} md={5} className="mb-2 mb-md-0">
                        <Form>
                            <Form.Group className="mb-3" controlId="searchFilterField">
                                <Row xs={12}>
                                    <Col xs={4} className="mb-2 mb-md-0">
                                        <Form.Select value={filterField} onChange={handleFilterFieldChange}>
                                            <option value="name">Name</option>
                                            <option value="path">Path</option>
                                            <option value="protocol">Protocol</option>
                                            <option value="owner">Owner</option>
                                        </Form.Select>
                                    </Col>
                                    <Col xs={8}>
                                        <Form.Control
                                            type="text"
                                            placeholder="Filter nodes..."
                                            value={filterValue}
                                            onChange={handleFilterValueChange}
                                        />
                                    </Col>
                                </Row>
                            </Form.Group>
                        </Form>
                    </Col>
                    <Col xs={12} md={4} className="mb-2 mb-md-0">
                        <Button variant="outline-light" onClick={handleRefresh} disabled={nodesLoading || protocolsLoading}>
                            Refresh
                        </Button>
                    </Col>
                    <Col xs={12} md={3}>
                        <Row>
                            <Col xs={6}>
                                <Button onClick={() => page > 0 && setPage(page - 1)} disabled={page === 0}>
                                    Previous
                                </Button>
                            </Col>
                            <Col xs={2} className="d-flex align-items-center justify-content-center">
                                <span>{page}</span>
                            </Col>
                            <Col xs={4}>
                                <Button onClick={() => setPage(page + 1)}>
                                    Next
                                </Button>
                            </Col>
                        </Row>
                    </Col>
                </Row>

                <Row className="mb-3">
                    <Col>
                        {nodesError ? (
                            <div className="text-danger">Unable to load nodes.</div>
                        ) : protocolsError ? (
                            <div className="text-danger">Unable to load protocols.</div>
                        ) : nodesLoading || protocolsLoading ? (
                            <div>Loading nodes...</div>
                        ) : null}
                    </Col>
                </Row>

                <Row>
                    <Col>
                        <BaseTable {...nodesDisplay} />
                    </Col>
                </Row>
            </Container>
        </>
    );
};

export default NodesListView;
