// Need to use the React-specific entry point to import createApi
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export type requestConfigsInfo = {
    pageCount: number;
    pageSize: number;
}

export type dashboardCameraConfigs = {
    idvideoDashboard: number;
    configJsonFetch: string; //Convert this to JSON since its a JSON based value
    idOwnerUser: number;
}

// configJsonFetch form
export type configCameraData = {
    width?: number;
    height?: number;
    idList?: Array<number>;
    idText?: number;
    rowLen?: number;
}

// Define a service using a base URL and expected endpoints
export const camerasDashboardService = createApi({
  reducerPath: 'camerasDashboardApi',
  baseQuery: fetchBaseQuery({ baseUrl: 'http://localhost:8080/DeviceNodeServer/phpWebApp/' }),
  endpoints: (builder) => ({
    fetchConfigs: builder.mutation<Array<dashboardCameraConfigs> , requestConfigsInfo>({
      query: (requestCamsInfo) => ({
        url: 'camerasDashboardService.php',
        method: 'POST',
        dataType: 'JSON',
        withcredentials: true,
        body: {...requestCamsInfo, actionOption:"fetchConfigs", userId: parseInt(sessionStorage.getItem("userId") as string)}
      }),
    }),
  })
})

// Export hooks for usage in functional components, which are
// auto-generated based on the defined endpoints
export const { useFetchConfigsMutation } = camerasDashboardService