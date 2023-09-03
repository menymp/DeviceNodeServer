import React from 'react';
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min";
import logo from './logo.svg';
import './App.css';
import NavMenu from './components/Nav/Nav';
import { Container, Row, Col } from 'react-bootstrap';
import BaseTable from './components/Table/Table'
import NodesListView from './components/Views/NodesListView'


function App() {

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
            <NodesListView></NodesListView>
          </Col>
        </Row>
      </Container>
    </>
  );
}

export default App;
