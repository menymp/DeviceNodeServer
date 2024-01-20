import { Container, Row, Col, Button } from 'react-bootstrap';

export interface rowObject {
    type: string
}

export interface tableInit {
    headers: Array<string>,
    rows: Array<Array<string>>,
    detailBtn?: boolean,
    detailCallback?: (selectedObject: string[]) => void,
    deleteBtn?: boolean,
    deleteCallback?: (selectedObject: string[]) => void,
    editBtn?: boolean,
    editCallback?: (selectedObject: string[]) => void,
    selectBtn?: boolean,
    selectCallback?: (selectedObject: string[]) => void
}

const BaseTable: React.FC<tableInit> = (props) => {
    const {headers, rows, detailBtn, deleteBtn, deleteCallback, detailCallback, editBtn, editCallback, selectCallback, selectBtn} = props
    return (
        <Container>
            <Row className='p-3 mb-2 bg-dark bg-gradient text-white rounded-2'>
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
                {
                    selectBtn === true ? 
                        <Col></Col> : null

                }
            </Row>
            {rows.map((columns) => { 
                return (
                    <Row className="p-3 mb-2 bg-secondary bg-gradient text-white rounded-3">
                        {columns.map((column) => {
                            return (
                                <Col>{column}</Col>
                            )
                        })}
                        {
                            detailBtn === true ? 
                                <Col><Button onClick={() => { detailCallback && detailCallback(columns)} }>Details</Button></Col> : null

                        }
                        {
                            editBtn === true ? 
                                <Col><Button onClick={() => { editCallback && editCallback(columns)}}>Edit</Button></Col> : null

                        }
                        {
                            deleteBtn === true ? 
                                <Col><Button onClick={() => { deleteCallback && deleteCallback(columns)}}>Delete</Button></Col> : null

                        }
                        {
                            selectBtn === true ? 
                                <Col><Button onClick={() => { selectCallback && selectCallback(columns)}}>Select</Button></Col> : null

                        }
                    </Row>
                )
            })}
        </Container>  
    )
}

export default BaseTable;