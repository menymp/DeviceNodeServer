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
import DashboardView from  './components/Views/DashboardView'
import DashboardEditor from './components/Views/DashboardEditor';
import Login from './components/Login/Login'
import CamerasListView from './components/Views/CamerasListView';
import CamerasDashboardView from './components/Views/CamerasDashboardView';
import { useEffect } from 'react';
import { useNavigate } from "react-router-dom";
import { isSessionActive } from './utils/sessionUtils'

function App() {
  const navigate = useNavigate();

  useEffect(() => {
    if (!isSessionActive()) {
      navigate('/Login');
    }
  }, [sessionStorage]);

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
          { isSessionActive() ? (
            <Routes>
                <Route path="/" element={<About></About>} />
                <Route path="/Cameras" element={<CamerasListView></CamerasListView>} />
                <Route path="/Nodes" element={<NodesListView></NodesListView>} />
                <Route path="/Devices" element={<DevicesListView></DevicesListView>} />
                <Route path="/Userinfo" element={<UserInfo></UserInfo>} />
                <Route path="/Dashboard" element={<DashboardView />} />
                <Route path="/DashboardEditor" element={<DashboardEditor />} />
                <Route path="/CamerasDashboard" element={<CamerasDashboardView />} />
            </Routes>
          ) : (
            <Routes>
                <Route path="/Login" element={<Login></Login>} />
            </Routes>
          )}
          </Col>
        </Row>
      </Container>
    </>
  );
}

export default App;
