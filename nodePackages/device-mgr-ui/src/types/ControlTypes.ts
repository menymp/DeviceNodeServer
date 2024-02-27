
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
}[];

export enum CONTROL_TYPE {
    DIGITALOUTPUT = 'DIGITALOUTPUT',
    PLAINTEXT = 'PLAINTEXT',
    SENSORREAD = 'SENSORREAD'
}

export interface ControlParameters {

}

export interface GenericUIControlParameters {
    control: Control,
    ws: WebSocket
}

export interface updateResponse {
    result: string,
    state: string
}

export const uiControlResponseHandler = (evt: any, idDevice: number, handleResponse: (response: updateResponse) => void) => {
    //process the response
    const responses = JSON.parse(evt.data);

    if (!responses || !responses.length) {
        return;
    }
        
    responses.forEach((response: any) => {
        /*get the corresponding class of the response and updates it*/
        if (response.idDevice === idDevice) {
            handleResponse(response);
            return;
        }
    });
}

export const generateUpdateCommand = (idDevice: number, cmdUpdate: string, args: string):deviceCommand => {
    return {
        idDevice: idDevice,
        command: cmdUpdate,
        args: args
    }
}

export const ws_send = (ws: WebSocket, msg: any) => {
    if( typeof(ws) == 'undefined' || ws.readyState === undefined || ws.readyState > 1) {
        console.error('error websocket is closed');
    }
    ws.send( JSON.stringify(msg) );
}