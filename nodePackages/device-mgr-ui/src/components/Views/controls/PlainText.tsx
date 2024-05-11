import { useState } from 'react';
import { Form } from 'react-bootstrap';
import { 
    GenericUIControlParameters, 
    updateResponse
} from '../../../types/ControlTypes'
import useControlUtils from "../../../hooks/useControlUtils";

type PlainTextParameters = {
    idDevice: string, 
    updateCmdStr: string, 
    apperance: string
}



const PlainText = (props: GenericUIControlParameters) => {
    const { control, id } = props;
    const [currentValue, setCurrentValue] = useState<string>('');

    const getControlParameters = () => {
        return JSON.parse(control.parameters) as PlainTextParameters;
    }

    const update = (response: updateResponse) => {
        if(response.state === 'SUCCESS')
        {
            setCurrentValue(response.result);
        }
    }

    const { commandHandler } = useControlUtils({ getControlParameters, ws: props.ws, update});
    
    return (
        <>
            <Form>
                <Form.Label>{control.name}</Form.Label>
                <Form.Control // prettier-ignore
                    type="switch"
                    id={`plain-text${control.idControl}${id}`}
                    value={currentValue}
                />
            </Form>
        </>
    )
}

export default PlainText;