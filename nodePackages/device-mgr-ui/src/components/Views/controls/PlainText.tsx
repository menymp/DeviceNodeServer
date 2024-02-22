import React from "react";
import { useState, useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import { GenericUIControlParameters, updateResponse } from '../../../types/ControlTypes'

type PlainTextParameters = {
    idDevice: string, 
    updateCmdStr: string, 
    apperance: string
}



const PlainText = forwardRef((props: GenericUIControlParameters, ref) => {
    const { control, commandHandler } = props;
    const [currentValue, setCurrentValue] = useState<string>('');
    const getControlParameters = () => {
        return JSON.parse(control.parameters) as PlainTextParameters;
    }

    const update = (response: updateResponse) => {
        if(response.state === 'SUCCESS')
        {
            setCurrentValue(response.result);
        }
    }

    useImperativeHandle(ref, () => ({
        update
    }));
    
    return (
        <>
            <Form>
                <Form.Label>{control.name}</Form.Label>
                <Form.Control // prettier-ignore
                    type="switch"
                    id={`plain-text${control.idControl}`}
                    value={currentValue}
                />
            </Form>
        </>
    )
})

export default PlainText;