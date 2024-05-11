import { useState } from 'react';
import { Form } from 'react-bootstrap';
import ColoredLed from 'colored-led';
import { 
    GenericUIControlParameters, 
    updateResponse
} from '../../../types/ControlTypes'
import useControlUtils from "../../../hooks/useControlUtils";

type DigitalInputParameters = {
    idDevice: string, 
    updateCmdStr: string, 
    apperance: string,
    onValue: string
}



const DigitalInput = (props: GenericUIControlParameters) => {
    const { control, id } = props;
    const [currentValue, setCurrentValue] = useState<string>('');

    const getControlParameters = () => {
        return JSON.parse(control.parameters) as DigitalInputParameters;
    }
    const parameters = getControlParameters();
    const ledState = currentValue === parameters.onValue;

    const update = (response: updateResponse) => {
        if(response.state === 'SUCCESS')
        {
            setCurrentValue(response.result);
        }
    }

    const { commandHandler } = useControlUtils({ getControlParameters, ws: props.ws, update});
    
    return (
        <>
            <Form id={id}>
                <Form.Label>{control.name}</Form.Label>
                <ColoredLed color={ledState ? 'red':'black'}></ColoredLed>
                <Form.Label>{currentValue}</Form.Label>
            </Form>
        </>
    )
}

export default DigitalInput;