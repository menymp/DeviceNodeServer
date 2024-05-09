import { useState } from 'react';
import { Button, Form } from 'react-bootstrap';
import { 
    GenericUIControlParameters, 
    updateResponse
} from '../../../types/ControlTypes'
import useControlUtils from "../../../hooks/useControlUtils";

type TextSenderParameters = {
    idDevice: string, 
    updateCmdStr: string, 
    apperance: string
}

const TextSender = (props: GenericUIControlParameters) => {
    const { control } = props;
    const [currentValue, setCurrentValue] = useState<string>('');
    const [inputText, setInputText] = useState<string>('');

    const getControlParameters = () => {
        return JSON.parse(control.parameters) as TextSenderParameters;
    }

    const update = (response: updateResponse) => {
        if(response.state === 'SUCCESS')
        {
            setCurrentValue(response.result);
        }
    }

    const { commandHandler } = useControlUtils({ getControlParameters, ws: props.ws, update});

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