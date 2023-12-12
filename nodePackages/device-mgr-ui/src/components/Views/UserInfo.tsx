import React from "react";
import { useState, useEffect } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable from '../Table/Table';
import { useGetUserInfoMutation } from "../../services/userService";

const DevicesListView: React.FC = () => {
    const [getUserInfo] = useGetUserInfoMutation()

    useEffect(() => {
        requestUserInfo();
    },[])
    
    const requestUserInfo = async () => {
        try {
            const result = await getUserInfo().unwrap()
            alert(JSON.stringify(result))
        }catch(e) {
            alert(e)
        }
    }

    return(
        <>
            <Form>
                <Form.Group className="mb-3" controlId="userInfo.name">
                        <Form.Label>Username</Form.Label>
                            <Form.Control
                                type="text"
                                value={sessionStorage.getItem("user") as string}
                                placeholder="name ..."
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="userInfo.mail">
                            <Form.Label>email</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="user@mail ..."
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="userInfo.registerDate">
                            <Form.Label>Register Date</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="registerDate..."
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="userInfo.telegramToken">
                            <Form.Label>telegram token</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="telegram token ..."
                                autoFocus
                            />
                        </Form.Group>
                        <Form.Group>
                            <Button variant="secondary">
                                save changes
                            </Button>
                        </Form.Group>
                    </Form>
        </>
    )
}

export default DevicesListView