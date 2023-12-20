import { Col, Button, Row, Container, Card, Form } from "react-bootstrap";
import { useLoginUserMutation } from "../../services/userService";
import React, { useState, useEffect } from 'react';
import { SUCCESS_RESULT } from '../../constants'

export default function Login() {
    const [loginUser] = useLoginUserMutation()
    const [username, setUsername] = useState<string>('')
    const [password, setPassword] = useState<string>('')
    //ToDo: missing user validation
    const handleLogin = async (event: any) => {
        event.preventDefault(); // 👈️ prevent page refresh
        try {
            // alert("log in" + ' ' + username + ' ' + password)
            const result = await loginUser({
                mailuid: username,
                pwd: password
            }).unwrap()
            if (result.result === SUCCESS_RESULT) {
                sessionStorage.setItem("user", username)
                sessionStorage.setItem("userId", result.userId.toString())
            } else {
                alert("Error: failed login!")
            }
        }catch(e) {
            alert(e)
        }
    }

    return (
        <>
        <Container>
            <Row className="vh-100 d-flex justify-content-center align-items-center">
            <Col md={8} lg={6} xs={12}>
                <div className="border border-3 border-primary"></div>
                <Card className="shadow">
                <Card.Body>
                    <div className="mb-3 mt-md-4">
                    <h2 className="fw-bold mb-2 text-uppercase ">Device Node System</h2>
                    <p className=" mb-5">Please enter your login and password!</p>
                    <div className="mb-3">
                        <Form onSubmit={handleLogin}>
                        <Form.Group className="mb-3" controlId="formBasicEmail">
                            <Form.Label className="text-center">
                            Email address
                            </Form.Label>
                            <Form.Control type="text" placeholder="Enter username" onChange={e => { setUsername(e.target.value)}}/>
                        </Form.Group>

                        <Form.Group
                            className="mb-3"
                            controlId="formBasicPassword"
                        >
                            <Form.Label>Password</Form.Label>
                            <Form.Control type="password" placeholder="Password" onChange={e => { setPassword(e.target.value)}}/>
                        </Form.Group>
                        <Form.Group
                            className="mb-3"
                            controlId="formBasicCheckbox"
                        >
                            <p className="small">
                            <a className="text-primary" href="#!">
                                Forgot password?
                            </a>
                            </p>
                        </Form.Group>
                        <div className="d-grid">
                            <Button variant="primary" type="submit">
                            Login
                            </Button>
                        </div>
                        </Form>
                        <div className="mt-3">
                        <p className="mb-0  text-center">
                            Don't have an account?{" "}
                            <a href="{''}" className="text-primary fw-bold">
                            Sign Up
                            </a>
                        </p>
                        </div>
                    </div>
                    </div>
                </Card.Body>
                </Card>
            </Col>
            </Row>
        </Container>
        </>
    );
}