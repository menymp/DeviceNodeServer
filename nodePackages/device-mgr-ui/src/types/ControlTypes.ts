
import { Control } from "../services/dashboardService"
import { ReactComponentElement } from "react"

// control general and specific types

export type reactUIControlls = React.ReactElement[];

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