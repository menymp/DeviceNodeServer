import React from "react";
import { useState, useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import { GenericUIControlParameters, updateResponse } from '../../../types/ControlTypes'

type DigitalOutputsControlParameters {
    idDevice: string, 
    cmdOnStr: string, 
    cmdOffStr: string, 
    updateCmdStr: string, 
    apperance: string
}



const DigitalOutput = forwardRef((props: GenericUIControlParameters, ref) => {
    const { control, commandHandler } = props;
    const getControlParameters = () => {
        return JSON.parse(control.parameters) as DigitalOutputsControlParameters;
    }
    
    const userClick = (e: React.ChangeEvent<HTMLInputElement>) => {
        //console.log("clickk");
        // ToDo: check if names exists
        const { idDevice, cmdOnStr, cmdOffStr } = getControlParameters()
        if(e.target.checked)
            commandHandler(parseInt(idDevice),cmdOnStr, "");
        else
            commandHandler(parseInt(idDevice),cmdOffStr, "");
    }

    // this function should be triggered from parent, research how are the approaches for this:
    // https://stackoverflow.com/questions/68642060/trigger-child-function-from-parent-component-using-react-hooks
    const update = (response: updateResponse) => {
        //checkBox = this.control.querySelectorAll('checkbox[deviceId]='+this.idDevice); //selects the checkbox
        const { cmdOnStr } = getControlParameters()
        let check = false;
        if(response.result === cmdOnStr)
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
    }

    useImperativeHandle(ref, () => ({
        update
    }));
    
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
})

export default DigitalOutput;