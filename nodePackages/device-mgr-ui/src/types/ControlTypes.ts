
import { Control } from "../services/dashboardService"
import { ReactComponentElement } from "react"

// control general and specific types

export type deviceCommand = {
    idDevice: number,
    command: string,
    args: string
}

export type reactUIControlls =  { 
    idLinkedDevice: number,
    component: React.ReactElement,
    reference: React.MutableRefObject<any> 
}[];

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