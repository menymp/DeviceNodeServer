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
    const [currentTimeout, setCurrentTimeout] = useState<NodeJS.Timeout>();
    const [responseTimeout, setResponseTimeout] = useState<NodeJS.Timeout>();

    const getControlParameters = () => {
        return JSON.parse(control.parameters) as PlainTextParameters;
    }
    const parameters = getControlParameters();
    const updateCommand = JSON.stringify([generateUpdateCommand(parseInt(parameters.idDevice), parameters.updateCmdStr, "")]);

    useEffect(() => {
        // run command scheduler for the first time
        props.ws.addEventListener('message' , (evt) => {
            uiControlResponseHandler(evt,  parseInt(parameters.idDevice), update);
        });
    
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
        setCurrentTimeout(setTimeout(() => {
            commandScheduler();
        }, 3*POLL_INTERVAL_MS));
    }

    const update = (response: updateResponse) => {
        if (currentTimeout) {
            clearTimeout(currentTimeout);
        }
        if (responseTimeout) {
            clearTimeout(responseTimeout);
        }

        if(response.state === 'SUCCESS')
        {
            setCurrentValue(response.result);
        }
        setCurrentTimeout(setTimeout(() => {
            commandScheduler();
        }, POLL_INTERVAL_MS));
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