import { useEffect, useRef } from 'react';
import { 
    updateResponse, 
    uiControlResponseHandler, 
    deviceCommand, 
    generateUpdateCommand, 
    ws_send 
} from '../types/ControlTypes'
import { POLL_INTERVAL_MS } from '../constants'

type controlUtilsParameters = {
    getControlParameters: () => {idDevice: string, updateCmdStr: string},
    ws: WebSocket,
    update: (args: updateResponse) => void
}

const useControlUtils = ({getControlParameters, ws, update}:controlUtilsParameters) => {
    const currentTimeout = useRef<NodeJS.Timeout>();
    const responseTimeout = useRef<NodeJS.Timeout>();
    const userCommands = useRef<deviceCommand | null>(null);

    const parameters = getControlParameters();
    const updateCommand = JSON.stringify([generateUpdateCommand(parseInt(parameters.idDevice), parameters.updateCmdStr, "")]);

    const commandHandler = (idDevice: number, command: string, args: string) => {
        userCommands.current = {idDevice, command, args};
    }

    const baseUpdateCallback = (args: updateResponse) => {
        if (currentTimeout.current) {
            clearTimeout(currentTimeout.current);
        }
        if (responseTimeout.current) {
            clearTimeout(responseTimeout.current);
        }
        update(args);
        currentTimeout.current = setTimeout(() => {
            commandScheduler();
        }, POLL_INTERVAL_MS);
    }

    useEffect(() => {
        // run command scheduler for the first time
        ws.addEventListener('message' , (evt) => {
            uiControlResponseHandler(evt,  parseInt(parameters.idDevice), baseUpdateCallback);
        });
        commandScheduler();
    }, []);
    
    const commandScheduler = () => {
        //if user data
        let jsonStr = "";
        if(userCommands.current)
        {
            jsonStr = JSON.stringify( [userCommands.current] );
            userCommands.current = null;
        }
        else
        {

            jsonStr = updateCommand; //already stringified
        }
        ws_send(ws, jsonStr);
        responseTimeout.current = setTimeout(() => {
            commandScheduler();
        }, 3*POLL_INTERVAL_MS);
    }
    
    return { commandHandler }
}

export default useControlUtils;