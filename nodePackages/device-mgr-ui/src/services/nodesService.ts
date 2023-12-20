// Need to use the React-specific entry point to import createApi
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export type requestNodesInfo = {
    pageCount: number;
    pageSize: number;
}

export type node = {
    idNodesTable: number
    nodePath: string
    idDeviceProtocol: number
    idOwnerUser: number
    connectionParameters: any
}

// Define a service using a base URL and expected endpoints
export const nodesService = createApi({
  reducerPath: 'userApi',
  baseQuery: fetchBaseQuery({ baseUrl: 'http://localhost:8080/DeviceNodeServer/phpWebApp/' }),
  endpoints: (builder) => ({
    fetchNodes: builder.mutation<Array<node> , requestNodesInfo>({
      query: (requestNodeInfo) => ({
        url: 'nodeService.php',
        method: 'POST',
        dataType: 'JSON',
        withcredentials: true,
        body: {...requestNodeInfo, type:"fetchNodes", userId: parseInt(sessionStorage.getItem("userId") as string)}
      }),
    }),
  }),
})

// Export hooks for usage in functional components, which are
// auto-generated based on the defined endpoints
export const { useFetchNodesMutation } = nodesService