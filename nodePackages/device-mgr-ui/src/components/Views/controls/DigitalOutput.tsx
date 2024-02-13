import React from "react";
import { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import { DigitalOutputParameters } from '../../../types/ControlTypes'

type DigitalOutputsControlParameters {
    idDevice: string, 
    cmdOnStr: string, 
    cmdOffStr: string, 
    updateCmdStr: string, 
    apperance: string
}

const DashboardView: React.FC<DigitalOutputParameters> = ({ commandHandler, control }) => {
    const [switchState, setSwitchState] = useState<boolean>(false);

    const getControlParameters = () => {
        return JSON.parse(control.parameters) as DigitalOutputsControlParameters;
    }
        // /*toggle switch apperance*/
        // class ctrlDigitalOutput
        // {
        //     constructor(name, controlParameters, usrCommandHandler)
        //     {
        //         this.name = name;
        //         this.idDevice = controlParameters["idDevice"];
        //         this.cmdOn = controlParameters["onCmdStr"];
        //         this.cmdOff = controlParameters["offCmdStr"];
        //         this.cmdUpdate = controlParameters["updateCmdStr"];
        //         this.cmdUpdateArgs = controlParameters["updateArgsStr"];
        //         this.usrCommandHandler = usrCommandHandler
        //     }
                // This should be implemented in the react render
        //     constructUiApperance()
        //     {
        //         var ControlElementContainer = document.createElement('form');
        //         var ControlElementContainerText = document.createElement('label');
        //         ControlElementContainer.innerHTML = this.name;
        //         var toggleSw = document.createElement('label');
        //         toggleSw.setAttribute('class','switch');
        //         var tmpCheckBox = document.createElement('input');
        //         tmpCheckBox.setAttribute('type','checkbox');
                
        //         tmpCheckBox.onclick = this.userClick.bind(this);/*check why this is needed*/
                
        //         tmpCheckBox.setAttribute('deviceId',this.idDevice);
        //         var tmpSpan = document.createElement('span');
        //         tmpSpan.setAttribute('class','slider round');
                    
        //         toggleSw.appendChild(tmpCheckBox);
        //         toggleSw.appendChild(tmpSpan);
        //         ControlElementContainer.appendChild(toggleSw);
                
        //         //$("#controlsContainer").append(ControlElementContainer);
        //         this.uiRefControl = tmpCheckBox;
                
        //         return ControlElementContainer;
        //     }
            
        //     /*ToDo: review if a best approach is to move this function to a super class*/
               /* INDEED THIS IS A BETTER APPROACH, MOVE THIS TO ControlTypes */
        //     getUpdateCommand()
        //     {
        //         var cmdObj = new Object();
        //         cmdObj.idDevice = parseInt(this.idDevice);
        //         cmdObj.command = this.cmdUpdate;
        //         cmdObj.args = ""; /*ToDo: check*/
        //         return cmdObj;
        //     }
        // }
    
    const userClick = () => {
        //console.log("clickk");
        // ToDo: check if names exists
        const { idDevice, cmdOnStr, cmdOffStr } = getControlParameters()
        if(switchState)
            commandHandler(parseInt(idDevice),cmdOnStr, "");
        else
            commandHandler(parseInt(idDevice),cmdOffStr, "");
    }

    // this function should be triggered from parent, research how are the approaches for this:
    // https://stackoverflow.com/questions/68642060/trigger-child-function-from-parent-component-using-react-hooks
    const update = (response) => {
        //checkBox = this.control.querySelectorAll('checkbox[deviceId]='+this.idDevice); //selects the checkbox
        let check = false;
        if(response.result === this.cmdOn)
        {
            check = true;
        }
        if(response.state === 'SUCCESS')
        {
            this.uiRefControl.checked = check
        }
    }
    
    return (
        <>
        </>
    )
}