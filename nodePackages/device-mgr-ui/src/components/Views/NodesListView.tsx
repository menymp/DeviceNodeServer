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
                <Col>
                    <Button>New Node</Button>
                </Col>
                <Col size={1} >
                    <Form >
                        <Form.Group className="mb-3 form-check-inline" controlId="searchFilterField">
                            <Form.Check type={"radio"} id={`name-radio`} label={`name`}/>
                            <Form.Check type={"radio"} id={`type-radio`} label={`type`}/>
                            <Form.Label>Name</Form.Label>
                            <Form.Control type="text" placeholder="node name..." />
                        </Form.Group>
                    </Form>
                </Col>
                <Col>
                    <Button>Next page</Button>
                    <Form>
                        <Form.Label> 10 </Form.Label>
                    </Form>
                    <Button>Previous page</Button>
                </Col>
            </Row>
            <Row>
                <Col><BaseTable {...tableContentExample}></BaseTable></Col>
            </Row>
        </Container>
    )
}

export default NodesListView