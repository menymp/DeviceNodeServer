import React from "react";
import { useState, useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import ColoredLed from 'colored-led';
import { 
    GenericUIControlParameters, 
    updateResponse, 
    uiControlResponseHandler, 
    deviceCommand, 
    generateUpdateCommand, 
    ws_send 
} from '../../../types/ControlTypes'
import { POLL_INTERVAL_MS } from '../../../constants'

type DigitalInputParameters = {
    idDevice: string, 
    updateCmdStr: string, 
    apperance: string,
    onValue: string
}



const DigitalInput = (props: GenericUIControlParameters) => {
    const { control } = props;
    const [userCommands, setUserCommands] = useState<Array<deviceCommand>>([]);
    const [currentValue, setCurrentValue] = useState<string>('');
    const currentTimeout = useRef<NodeJS.Timeout>();
    const responseTimeout = useRef<NodeJS.Timeout>();

    const getControlParameters = () => {
        return JSON.parse(control.parameters) as DigitalInputParameters;
    }
    const parameters = getControlParameters();
    const updateCommand = JSON.stringify([generateUpdateCommand(parseInt(parameters.idDevice), parameters.updateCmdStr, "")]);
    const ledState = currentValue === parameters.onValue

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
        responseTimeout.current = setTimeout(() => {
            commandScheduler();
        }, 3*POLL_INTERVAL_MS);
    }

    const update = (response: updateResponse) => {
        if (currentTimeout.current) {
            clearTimeout(currentTimeout.current);
        }
        if (responseTimeout.current) {
            clearTimeout(responseTimeout.current);
        }

        if(response.state === 'SUCCESS')
        {
            setCurrentValue(response.result);
        }
        currentTimeout.current = setTimeout(() => {
            commandScheduler();
        }, POLL_INTERVAL_MS);
    }
    
    return (
        <>
            <Form>
                <Form.Label>{control.name}</Form.Label>
                <ColoredLed color={ledState ? 'red':'black'}></ColoredLed>
                <Form.Label>{currentValue}</Form.Label>
            </Form>
        </>
    )
}

export default DigitalInput;