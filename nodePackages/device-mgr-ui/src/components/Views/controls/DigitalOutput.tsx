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

type DigitalOutputsControlParameters = {
    idDevice: string, 
    onCmdStr: string, 
    offCmdStr: string, 
    updateCmdStr: string, 
    apperance: string
}

const DigitalOutput = (props: GenericUIControlParameters) => {
    const { control } = props;
    const userCommands = useRef<deviceCommand | null>(null);
    const currentTimeout = useRef<NodeJS.Timeout>();
    const responseTimeout = useRef<NodeJS.Timeout>();

    const getControlParameters = () => {
        return JSON.parse(control.parameters) as DigitalOutputsControlParameters;
    }
    const parameters = getControlParameters();
    const updateCommand = JSON.stringify([generateUpdateCommand(parseInt(parameters.idDevice), parameters.updateCmdStr, "")]);

    const commandHandler = (idDevice: number, command: string, args: string) => {
        //loads the collection with a new command
        userCommands.current = {idDevice, command, args};
    }

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
            jsonStr = JSON.stringify( [userCommands.current] );
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

    const userClick = (e: React.ChangeEvent<HTMLInputElement>) => {
        //console.log("clickk");
        // ToDo: check if names exists
        const { idDevice, onCmdStr, offCmdStr } = getControlParameters()
        if(e.target.checked)
            commandHandler(parseInt(idDevice),onCmdStr, "");
        else
            commandHandler(parseInt(idDevice),offCmdStr, "");
    }

    // this function should be triggered from parent, research how are the approaches for this:
    // https://stackoverflow.com/questions/68642060/trigger-child-function-from-parent-component-using-react-hooks
    const update = (response: updateResponse) => {
        if (currentTimeout.current) {
            clearTimeout(currentTimeout.current);
        }
        if (responseTimeout.current) {
            clearTimeout(responseTimeout.current);
        }
        ///////////////////////////////////////
        /** begins user specific code * */
        //checkBox = this.control.querySelectorAll('checkbox[deviceId]='+this.idDevice); //selects the checkbox
        const { onCmdStr } = getControlParameters()
        let check = false;
        if(response.result === onCmdStr)
        {
            check = true;
        }
        if(response.state === 'SUCCESS')
        {
            //this.uiRefControl.checked = check
            // perform the expected UI behavior here
            const uiToggleControl = document.querySelector(`#digital-output${control.idControl}`) as HTMLInputElement;
            uiToggleControl.checked = check;
        }
        /* ends user specific code */
        //////////////////////////////////////////////////
        currentTimeout.current = setTimeout(() => {
            commandScheduler();
        }, POLL_INTERVAL_MS);
    }
    
    return (
        <>
            <Form>
                <Form.Label>{control.name}</Form.Label>
                <Form.Check // prettier-ignore
                    type="switch"
                    id={`digital-output${control.idControl}`}
                    label="Check this switch"
                    onChange={userClick}
                />
            </Form>
        </>
    )
}

export default DigitalOutput;