import React from 'react';
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min";
import logo from './logo.svg';
import './App.css';
import NavMenu from './components/Nav/Nav';
import { Container, Row, Col } from 'react-bootstrap';
import BaseTable from './components/Table/Table'
import NodesListView from './components/Views/NodesListView'
import About from './components/Views/About'
import { Routes, Route } from "react-router-dom"
import DevicesListView from './components/Views/DevicesListView'
import UserInfo from './components/Views/UserInfo';


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
            <Routes>
              <Route path="/" element={<About></About>} />
              <Route path="/Nodes" element={<NodesListView></NodesListView>} />
              <Route path="/Devices" element={<DevicesListView></DevicesListView>} />
              <Route path="/Userinfo" element={<UserInfo></UserInfo>} />
            </Routes>
          </Col>
        </Row>
      </Container>
    </>
  );
}

export default App;
