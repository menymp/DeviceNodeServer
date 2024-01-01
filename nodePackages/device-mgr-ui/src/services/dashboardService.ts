// Need to use the React-specific entry point to import createApi
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export type requestControlsInfo = {
    pageCount: number;
    pageSize: number;
}

// Example of a control and parameters, some fields may change depending on the control configuration
/*{"idControl":8,"name":"simpleText","parameters":"{\"idDevice\": \"5\", \"apperance\": \"INPUTTEXT\", \"updateCmdStr\":
\"getValue\"}","typename":"PLAINTEXT","idType":3,"username":"menymp","controlTemplate":"{\"idDevice\": \"REFERENCE\",
\"apperance\": [\"INPUTTEXT\", \"CONSOLE\"], \"updateCmdStr\":
\"FIELD\"}"}*/

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
  reducerPath: 'cameraApi',
  baseQuery: fetchBaseQuery({ baseUrl: 'http://localhost:8080/DeviceNodeServer/phpWebApp/' }),
  endpoints: (builder) => ({
    fetchControls: builder.mutation<Array<Control> , requestControlsInfo>({
      query: (requestCamsInfo) => ({
        url: 'dashboardService.php',
        method: 'POST',
        dataType: 'JSON',
        withcredentials: true,
        body: {...requestCamsInfo, actionOption:"fetchControls", userId: parseInt(sessionStorage.getItem("userId") as string)}
      }),
    }),
  })
})

// Export hooks for usage in functional components, which are
// auto-generated based on the defined endpoints
export const { useFetchControlsMutation } = dashboardService