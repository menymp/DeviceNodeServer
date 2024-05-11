import React from "react";
import { Form } from 'react-bootstrap';
import { 
    GenericUIControlParameters, 
    updateResponse
} from '../../../types/ControlTypes'
import useControlUtils from "../../../hooks/useControlUtils";

type DigitalOutputsControlParameters = {
    idDevice: string, 
    onCmdStr: string, 
    offCmdStr: string, 
    updateCmdStr: string, 
    apperance: string
}

const DigitalOutput = (props: GenericUIControlParameters) => {
    const { control, id } = props;
    // for analog output use https://www.npmjs.com/package/react-dial-knob
    // depending on the output type, the component would have many apperances

    const getControlParameters = () => {
        return JSON.parse(control.parameters) as DigitalOutputsControlParameters;
    }
    const parameters = getControlParameters();

    // this function should be triggered from parent, research how are the approaches for this:
    // https://stackoverflow.com/questions/68642060/trigger-child-function-from-parent-component-using-react-hooks
    const update = (response: updateResponse) => {
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
    }

    const { commandHandler } = useControlUtils({ getControlParameters, ws: props.ws, update});

    const userClick = (e: React.ChangeEvent<HTMLInputElement>) => {
        //console.log("clickk");
        // ToDo: check if names exists
        const { idDevice, onCmdStr, offCmdStr } = getControlParameters()
        if(e.target.checked)
            commandHandler(parseInt(idDevice),onCmdStr, "");
        else
            commandHandler(parseInt(idDevice),offCmdStr, "");
    }
    
    return (
        <>
            <Form>
                <Form.Label>{control.name}</Form.Label>
                <Form.Check // prettier-ignore
                    type="switch"
                    id={`digital-output${control.idControl}${id}`}
                    label="Check this switch"
                    onChange={userClick}
                />
            </Form>
        </>
    )
}

export default DigitalOutput;