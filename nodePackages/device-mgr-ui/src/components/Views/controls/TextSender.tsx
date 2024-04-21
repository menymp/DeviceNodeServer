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

type TextSenderParameters = {
    idDevice: string, 
    updateCmdStr: string, 
    apperance: string
}


//ToDo: since we already have too many components with shared logic, think of a way to
//      refractor this so this all will be a common toolbox for future controls
const TextSender = (props: GenericUIControlParameters) => {
    const { control } = props;
    const userCommands = useRef<deviceCommand | null>(null);
    const [currentValue, setCurrentValue] = useState<string>('');
    const currentTimeout = useRef<NodeJS.Timeout>();
    const responseTimeout = useRef<NodeJS.Timeout>();
    const [inputText, setInputText] = useState<string>('');

    const getControlParameters = () => {
        return JSON.parse(control.parameters) as TextSenderParameters;
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
        if(userCommands.current)
        {
            jsonStr = JSON.stringify([ userCommands.current ]);
            userCommands.current = null;
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

    const commandHandler = (idDevice: number, command: string, args: string) => {
        //loads the collection with a new command
        userCommands.current = {idDevice, command, args};
    }

    const userClickSend = () => {
        //console.log("clickk");
        // ToDo: check if names exists
        const { idDevice } = getControlParameters()

        commandHandler(parseInt(idDevice),inputText, "");
    }
    
    return (
        <>
            <Form>
                <Form.Label>{control.name}</Form.Label>
                <Form.Label>{currentValue}</Form.Label>
                <Form.Control // prettier-ignore
                    type="switch"
                    id={`text-sender${control.idControl}`}
                    onChange={(e) => {
                        setInputText(e.target.value)
                    }}
                    placeholder="text to send ..."
                />
                <Button variant="primary" onClick={userClickSend}>
                        Send
                </Button>
            </Form>
        </>
    )
}

export default TextSender;