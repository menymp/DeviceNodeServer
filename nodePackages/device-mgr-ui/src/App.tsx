import React from 'react';
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min";
import logo from './logo.svg';
import './App.css';
import NavMenu from './components/Nav/Nav';
import { Container, Row, Col } from 'react-bootstrap';
import BaseTable from './components/Table/Table'


function App() {

  const tableContentExample = {
    headers: ["header1", "header2", "header3"],
    rows: ["val1", "val2", "val3"],
    detailBtn: true,
    deleteBtn: true,
    editBtn: true
  }

  return (
    <>
      <Container fluid>     
        <Row>
          <Col>
            <NavMenu></NavMenu>
          </Col>
        </Row>   
        <Row>
          <Col>
            <BaseTable {...tableContentExample}></BaseTable>
          </Col>
        </Row>
      </Container>
    </>
  );
}

export default App;
