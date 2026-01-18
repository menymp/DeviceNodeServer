// Need to use the React-specific entry point to import createApi
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export type requestControlsInfo = {
  pageCount: number;
  pageSize: number;
}

export type requestControlByIdInfo = {
  idControl: number;
}

// example of control template
/*
[{"idControlsTypes":1,"TypeName":"DIGITALOUTPUT","controlTemplate":"{\"idDevice\": \"REFERENCE\", \"onCmdStr\":
\"FIELD\", \"apperance\": [\"TOGGLESWITCH\", \"BUTTON\"], \"offCmdStr\": \"FIELD\", \"updateCmdStr\":
\"FIELD\"}"},{"idControlsTypes":2,"TypeName":"SENSORREAD","controlTemplate":"{\"idDevice\": \"REFERENCE\", \"lowLimit\":
\"NUMBER\", \"apperance\": [\"TEXTVAL\", \"HBAR\", \"YBAR\", \"GAUGE\"], \"highLimit\": \"NUMBER\", \"updateCmdStr\":
\"FIELD\"}"},{"idControlsTypes":3,"TypeName":"PLAINTEXT","controlTemplate":"{\"idDevice\": \"REFERENCE\", \"apperance\":
[\"INPUTTEXT\", \"CONSOLE\"], \"updateCmdStr\":
\"FIELD\"}"},{"idControlsTypes":4,"TypeName":"DIGITALINPUT","controlTemplate":"{\"idDevice\": \"REFERENCE\",
\"apperance\": [\"LED\"], \"updateCmdStr\": \"FIELD\"}"}]
*/

/*
Example of id control template
[{"controlTemplate":"{\"idDevice\": \"REFERENCE\", \"lowLimit\": \"NUMBER\", \"apperance\": [\"TEXTVAL\", \"HBAR\",
\"YBAR\", \"GAUGE\"], \"highLimit\": \"NUMBER\", \"updateCmdStr\": \"FIELD\"}"}]
*/
/* ToDo: define each type in extenal file */
export type controlTemplateGenericMembers = {
  idDevice: string; // REFERENCE
  apperance: Array<string>;
  updateCmdStr: string; // FIELD
}

export enum TEMPLATE_FIEL_TYPE {
  REFERENCE = "REFERENCE",
  FIELD = "FIELD",
}

export type controlTemplate = {
  controlTemplate: string; /* ToDo: convert this string to object */
}

export type controlType = {
  idControlsTypes: number;
  TypeName: string;  // DIGITALOUTPUT, DIGITALINPUT, SENSORREAD, PLAINTEXT
  controlTemplate: controlTemplate
}

export type getControlTypeRequestInfo = {
  idControlType: number;
}

// Example of a control and parameters, some fields may change depending on the control configuration
/*{"idControl":8,"name":"simpleText","parameters":"{\"idDevice\": \"5\", \"apperance\": \"INPUTTEXT\", \"updateCmdStr\":
\"getValue\"}","typename":"PLAINTEXT","idType":3,"username":"menymp","controlTemplate":"{\"idDevice\": \"REFERENCE\",
\"apperance\": [\"INPUTTEXT\", \"CONSOLE\"], \"updateCmdStr\":
\"FIELD\"}"}*/

export type deleteControlInfo = {
  idControl: number;
}

export type saveControlInfo = {
  parameters: any;
  idType: number;
  Name: string;
  idControl: number;
}

export type Control = {
    idControl: number;
    name: string; 
    parameters: string; //Convert this to JSON since its a JSON based value
    typename: string;
    idType: number;
    username: string;
    controlTemplate: string; //Convert this to JSON since its a JSON based value
}

// Define a service using a base URL and expected endpoints
export const dashboardService = createApi({
  reducerPath: 'dashboardApi',
  baseQuery: fetchBaseQuery({ baseUrl: process.env.REACT_APP_DEVICE_SERVICE_URL }),
  endpoints: (builder) => ({
    fetchControls: builder.mutation<Array<Control> , requestControlsInfo>({
      query: (requestControlsArgs) => ({
        url: 'dashboardService.php',
        method: 'POST',
        dataType: 'JSON',
        withcredentials: true,
        body: {...requestControlsArgs, actionOption:"fetchControls", userId: parseInt(sessionStorage.getItem("userId") as string)}
      })
    }),
    fetchControlById: builder.mutation<Array<Control> , requestControlByIdInfo>({
      query: (requestControlByIdArgs) => ({
        url: 'dashboardService.php',
        method: 'POST',
        dataType: 'JSON',
        withcredentials: true,
        body: {...requestControlByIdArgs, actionOption:"fetchControlById", userId: parseInt(sessionStorage.getItem("userId") as string)}
      })
    }),
    fetchControlsTypes: builder.mutation<Array<controlType> , void>({
      query: () => ({
        url: 'dashboardService.php',
        method: 'POST',
        dataType: 'JSON',
        withcredentials: true,
        body: {actionOption:"fetchControlsTypes", userId: parseInt(sessionStorage.getItem("userId") as string)}
      })
    }),
    getControlTypeTemplate: builder.mutation<Array<controlTemplate> , getControlTypeRequestInfo>({
      query: (requestControlType) => ({
        url: 'dashboardService.php',
        method: 'POST',
        dataType: 'JSON',
        withcredentials: true,
        body: {...requestControlType, actionOption:"getControlTypeTemplate", userId: parseInt(sessionStorage.getItem("userId") as string)}
      })
    }),
    deleteControlById: builder.mutation<void , deleteControlInfo>({
      query: (requestDeleteControlsArgs) => ({
        url: 'dashboardService.php',
        method: 'POST',
        dataType: 'JSON',
        withcredentials: true,
        body: {...requestDeleteControlsArgs, actionOption:"deleteControlById", userId: parseInt(sessionStorage.getItem("userId") as string)}
      })
    }),
    saveControl: builder.mutation<void , saveControlInfo>({
      query: (requestSaveControlArgs) => ({
        url: 'dashboardService.php',
        method: 'POST',
        dataType: 'JSON',
        withcredentials: true,
        body: {...requestSaveControlArgs, actionOption:"saveControl", userId: parseInt(sessionStorage.getItem("userId") as string)}
      })
    })
  })
})

// Export hooks for usage in functional components, which are
// auto-generated based on the defined endpoints
export const { 
  useFetchControlsMutation, 
  useFetchControlByIdMutation, 
  useFetchControlsTypesMutation, 
  useGetControlTypeTemplateMutation, 
  useDeleteControlByIdMutation, 
  useSaveControlMutation 
} = dashboardService