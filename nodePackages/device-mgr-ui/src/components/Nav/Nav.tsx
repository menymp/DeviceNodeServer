import React from "react";
import Container from 'react-bootstrap/Container';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import NavDropdown from 'react-bootstrap/NavDropdown';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button'

const NavMenu: React.FC<{}> = () => {
    return (
        <Navbar bg="dark" variant="dark">
        <Nav className="container-fluid margin-left: 20px">
            <Navbar.Brand href="#home" className="margin-left 20px">
            <img
              alt=""
              src={require("../../resources/gear.png")}
              width="30"
              height="30"
              className="d-inline-block align-top"
            />
          </Navbar.Brand>
          <Navbar.Toggle aria-controls="basic-navbar-nav" />
          <Navbar.Collapse id="basic-navbar-nav">
            <Nav>
              <Nav.Link>Device Node</Nav.Link>
              <Nav.Link href="/Dashboard">Dashboard</Nav.Link>
              <Nav.Link href="/Devices">Devices</Nav.Link>
              <Nav.Link href="/Nodes">Nodes</Nav.Link>
              <Nav.Link href="#link">Cameras</Nav.Link>
              <Nav.Link href="#link">video Dash</Nav.Link>
              <Nav.Link href="/Userinfo">user info</Nav.Link>
              <Form className="mr-left ">
                <Form.Group className="mb-3 form-check-inline" controlId="userName">
                  <Row>
                    <Col>
                      <Form.Control type="text" placeholder="username..." />
                    </Col>
                    <Col>
                      <Form.Control type="password" placeholder="password..." />
                    </Col>
                    <Col>
                      <Button>Log In</Button>
                    </Col>
                  </Row>
                </Form.Group>
              </Form>
            </Nav>
          </Navbar.Collapse>
        </Nav>
      </Navbar>
    )
}

export default NavMenu;