import React from "react";
import { useState, useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import { 
    GenericUIControlParameters, 
    updateResponse, 
    uiControlResponseHandler, 
    deviceCommand, 
    generateUpdateCommand, 
    ws_send 
} from '../../../types/ControlTypes'
import { POLL_INTERVAL_MS } from '../../../constants'

type PlainTextParameters = {
    idDevice: string, 
    updateCmdStr: string, 
    apperance: string
}



const PlainText = (props: GenericUIControlParameters) => {
    const { control } = props;
    const [userCommands, setUserCommands] = useState<Array<deviceCommand>>([]);
    const [currentValue, setCurrentValue] = useState<string>('');
    const getControlParameters = () => {
        return JSON.parse(control.parameters) as PlainTextParameters;
    }
    const parameters = getControlParameters();
    const updateCommand = JSON.stringify([generateUpdateCommand(parseInt(parameters.idDevice), parameters.updateCmdStr, "")]);

    props.ws.addEventListener('message' , (evt) => {
        uiControlResponseHandler(evt,  parseInt(parameters.idDevice), update);
    });

    useEffect(() => {
        // run command scheduler for the first time
        commandScheduler();
    }, []);

    const commandScheduler = () => {
        //if user data
        let jsonStr = "";
        if(userCommands.length > 0)
        {
            jsonStr = JSON.stringify({ cmds: userCommands });
            setUserCommands([]);
        }
        else
        {

            jsonStr = updateCommand; //already stringified
        }
        ws_send(props.ws, jsonStr);
    }

    const update = (response: updateResponse) => {
        if(response.state === 'SUCCESS')
        {
            setCurrentValue(response.result);
        }
        setTimeout(() => {
            commandScheduler();
        }, POLL_INTERVAL_MS);
    }
    
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
}

export default PlainText;