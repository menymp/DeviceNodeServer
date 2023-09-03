import React from "react";
import { Container, Row, Col, Button, Form } from 'react-bootstrap';
import BaseTable from '../Table/Table'

const NodesListView: React.FC = () => {
    const tableContentExample = {
        headers: ["header1", "header2", "header3"],
        rows: ["val1", "val2", "val3"],
        detailBtn: true,
        deleteBtn: true,
        editBtn: true
    }
    // a pagination item already exists
    
    return(
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
    )
}

export default NodesListView