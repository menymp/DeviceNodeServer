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
import GaugeChart from 'react-gauge-chart'
import { POLL_INTERVAL_MS } from '../../../constants'
import { param } from "jquery";

type SensorReadParameters = {
    idDevice: string, 
    updateCmdStr: string, 
    apperance: string,
    lowLimit: string | number,
    highLimit: string | number
}



const SensorRead = (props: GenericUIControlParameters) => {
    const { control } = props;
    const [userCommands, setUserCommands] = useState<Array<deviceCommand>>([]);
    const [currentValue, setCurrentValue] = useState<string>('');
    const currentTimeout = useRef<NodeJS.Timeout>();
    const responseTimeout = useRef<NodeJS.Timeout>();

    const getControlParameters = () => {
        return JSON.parse(control.parameters) as SensorReadParameters;
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
                <GaugeChart id={`gauge-chart${parameters.idDevice}${parameters.apperance}`} 
                    nrOfLevels={30} 
                    colors={["#FF5F6D", "#FFC371"]} 
                    arcWidth={0.3} 
                    percent={parseInt(currentValue) / (typeof parameters.highLimit === 'string' ? parseInt(parameters.highLimit) : parameters.highLimit)} 
                />
                <Form.Control // prettier-ignore
                    type="switch"
                    id={`plain-text${control.idControl}${parameters.apperance}`}
                    value={currentValue}
                />
            </Form>
        </>
    )
}

export default SensorRead;