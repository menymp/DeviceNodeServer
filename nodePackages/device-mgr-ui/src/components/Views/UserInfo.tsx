import React from "react";
import { useState, useEffect } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import BaseTable from '../Table/Table';
import { useGetUserInfoMutation, useUpdateUserInfoMutation, userInfo } from "../../services/userService";

enum FIELD_ID {
    EMAIL,
    TELEGRAM_TOKEN
}

const DevicesListView: React.FC = () => {
    const [getUserInfo] = useGetUserInfoMutation()
    const [updateUserInfo] = useUpdateUserInfoMutation()
    const [userFetchInfo, setUserFetchInfo] = useState<userInfo>()
    // for now the only seteable fields are user mail and telegram token
    const [newMail, setNewMail] = useState<string>()
    const [newTToken, setNewTToken] = useState<string>()

    useEffect(() => {
        requestUserInfo();
    },[])
    
    const requestUserInfo = async () => {
        try {
            if (!sessionStorage.getItem("user")) {
                return
            }
            const user = sessionStorage.getItem("user")!
            const req = {
                username: user
            }
            const result = await getUserInfo(req).unwrap()
            setUserFetchInfo(result[0])
        }catch(e) {
            alert(e)
        }
    }

    const saveUserInfoData = async (value: string, from: FIELD_ID) => {
        // ToDo: need proper data validation here!!!!

        if (from === FIELD_ID.EMAIL) {
            setNewMail(value)
        }
        if (from === FIELD_ID.TELEGRAM_TOKEN) {
            setNewTToken(value)
        }
    }

    const submitNewInfo = async () => {
        try {
            if (!userFetchInfo) {
                return
            }
            let newUserInfo = {...userFetchInfo}
            newUserInfo.email = newMail!
            newUserInfo.telegrambotToken = newTToken!
            updateUserInfo(newUserInfo).unwrap()
        } catch (e) {
            // update attempt error
        }
    }

    return(
        <>
            <Form>
                <Form.Group className="mb-3" controlId="userInfo.name">
                        <Form.Label>Username</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="name ..."
                                autoFocus
                                value={userFetchInfo?.username}
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="userInfo.mail">
                            <Form.Label>email</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="user@mail ..."
                                autoFocus
                                value={userFetchInfo?.email}
                                onChange={e => {saveUserInfoData(e.target.value, FIELD_ID.EMAIL)}}
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="userInfo.registerDate">
                            <Form.Label>Register Date</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="registerDate..."
                                autoFocus
                                value={userFetchInfo?.registerdate}
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="userInfo.telegramToken">
                            <Form.Label>telegram token</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="telegram token ..."
                                autoFocus
                                value={userFetchInfo?.telegrambotToken}
                                onChange={e => { saveUserInfoData(e.target.value, FIELD_ID.TELEGRAM_TOKEN)}}
                            />
                        </Form.Group>
                        <Form.Group>
                            <Button variant="secondary" onClick={e => { submitNewInfo()}}>
                                save changes
                            </Button>
                        </Form.Group>
                    </Form>
        </>
    )
}

export default DevicesListView