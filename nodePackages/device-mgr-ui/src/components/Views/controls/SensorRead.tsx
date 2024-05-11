import { useState } from 'react';
import { Form } from 'react-bootstrap';
import { 
    GenericUIControlParameters, 
    updateResponse
} from '../../../types/ControlTypes'
import { Gauge } from 'react-circular-gauge';
import chroma from 'chroma-js';
import useControlUtils from "../../../hooks/useControlUtils";

type SensorReadParameters = {
    idDevice: string, 
    updateCmdStr: string, 
    apperance: string,
    lowLimit: string | number,
    highLimit: string | number
}

// a better gauge https://stackblitz.com/edit/react-ts-jutcmi?file=index.tsx
// yet even better https://github.com/arcturus3/react-circular-gauge

const SensorRead = (props: GenericUIControlParameters) => {
    const { control, id } = props;
    const [currentValue, setCurrentValue] = useState<string>('');

    const getControlParameters = () => {
        return JSON.parse(control.parameters) as SensorReadParameters;
    }
    const parameters = getControlParameters();

    const update = (response: updateResponse) => {
        if(response.state === 'SUCCESS')
        {
            setCurrentValue(response.result);
        }
    }
    const { commandHandler } = useControlUtils({ getControlParameters, ws: props.ws, update});
    /*
                    <GaugeChart id= 
                    nrOfLevels={30} 
                    colors={["#FF5F6D", "#FFC371"]} 
                    arcWidth={0.3} 
                    percent={parseInt(currentValue) / (typeof parameters.highLimit === 'string' ? parseInt(parameters.highLimit) : parameters.highLimit)} 
                />
    */
    return (
        <>
            <Form>
                <Form.Label>{control.name}</Form.Label>
                <Gauge
                    id={`gauge-chart${parameters.idDevice}${parameters.apperance}`}
                    value={parseInt(currentValue)}
                    minValue={0}
                    maxValue={100}
                    renderBottomLabel="value"
                    arcColor={({ normValue }) => chroma.scale(['green', 'red'])(normValue).css()}
                />
                <Form.Control // prettier-ignore
                    type="switch"
                    id={`plain-text${control.idControl}${parameters.apperance}${id}`}
                    value={currentValue}
                />
            </Form>
        </>
    )
}

export default SensorRead;