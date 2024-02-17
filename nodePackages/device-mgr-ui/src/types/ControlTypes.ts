
import { Control } from "../services/dashboardService"

// control general and specific types

export enum CONTROL_TYPE {
    DIGITALOUTPUT = 'DIGITALOUTPUT',
    PLAINTEXT = 'PLAINTEXT',
    SENSORREAD = 'SENSORREAD'
}

export interface ControlParameters {

}

export interface DigitalOutputParameters {
    commandHandler: (controlId: number, command: string, args: string) => void,
    control: Control
}

export interface updateResponse {
    result: string,
    state: string
}