import { Container, Row, Col, Button } from 'react-bootstrap';

export interface rowObject {
    type: string
}

export interface tableInit {
    headers: Array<string>,
    rows: Array<string>,
    detailBtn: boolean,
    deleteBtn: boolean,
    editBtn: boolean
}

const BaseTable: React.FC<tableInit> = (props) => {
    const {headers, rows, detailBtn, deleteBtn, editBtn} = props
    return (
        <Container>
            <Row>
                {headers.map((header) => {
                    return (
                        <Col>{header}</Col>
                    )
                })}
                {
                    detailBtn === true ? 
                        <Col></Col> : null

                }
                {
                    editBtn === true ? 
                        <Col></Col> : null

                }
                {
                    deleteBtn === true ? 
                        <Col></Col> : null

                }
            </Row>
            <Row>
                {rows.map((row) => {
                    return (
                        <Col>{row}</Col>
                    )
                })}
                {
                    detailBtn === true ? 
                        <Col><Button>Details</Button></Col> : null

                }
                {
                    editBtn === true ? 
                        <Col><Button>Edit</Button></Col> : null

                }
                {
                    deleteBtn === true ? 
                        <Col><Button>Delete</Button></Col> : null

                }
            </Row>
        </Container>  
    )
}

export default BaseTable;