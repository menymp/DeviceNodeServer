import React from "react";
import { useState, useEffect } from 'react';
import { Button, Form } from 'react-bootstrap';
import { useGetMeQuery } from "../../services/userService";

enum FIELD_ID {
    EMAIL,
    TELEGRAM_TOKEN
}

const UserInfo: React.FC = () => {
    const { data: userFetchInfo } = useGetMeQuery();
    const [newMail, setNewMail] = useState<string>('');
    const [newTToken, setNewTToken] = useState<string>('');

    useEffect(() => {
        if (!userFetchInfo) {
            return;
        }
        setNewMail(userFetchInfo.email ?? '');
        setNewTToken(userFetchInfo.telegrambotToken ?? '');
    }, [userFetchInfo]);

    const saveUserInfoData = (value: string, from: FIELD_ID) => {
        if (from === FIELD_ID.EMAIL) {
            setNewMail(value)
        }
        if (from === FIELD_ID.TELEGRAM_TOKEN) {
            setNewTToken(value)
        }
    }

    const submitNewInfo = () => {
        alert('User update is not supported by the current service contract.');
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
                        value={userFetchInfo?.username ?? ''}
                        readOnly
                    />
                </Form.Group>
                <Form.Group className="mb-3" controlId="userInfo.mail">
                            <Form.Label>email</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="user@mail ..."
                                autoFocus
                                value={newMail}
                                onChange={e => {saveUserInfoData(e.target.value, FIELD_ID.EMAIL)}}
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="userInfo.registerDate">
                            <Form.Label>Register Date</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="registerDate..."
                                autoFocus
                                value={userFetchInfo?.registerdate ?? ''}
                                readOnly
                            />
                        </Form.Group>
                        <Form.Group className="mb-3" controlId="userInfo.telegramToken">
                            <Form.Label>telegram token</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="telegram token ..."
                                autoFocus
                                value={newTToken}
                                onChange={e => { saveUserInfoData(e.target.value, FIELD_ID.TELEGRAM_TOKEN)}}
                            />
                        </Form.Group>
                <Form.Group>
                    <Button variant="secondary" onClick={submitNewInfo}>
                        save changes
                    </Button>
                </Form.Group>
            </Form>
        </>
    )
}

export default UserInfo