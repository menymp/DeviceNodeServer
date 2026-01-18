// Need to use the React-specific entry point to import createApi
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export type requestConfigsInfo = {
    pageCount: number;
    pageSize: number;
}

// configJsonFetch form
export type configCameraData = {
  width?: number;
  height?: number;
  idList?: Array<number>;
  idText?: number;
  rowLen?: number;
}

export type dashboardCameraConfigs = {
    idvideoDashboard: number;
    configJsonFetch: configCameraData;
    idOwnerUser: number;
}

// Define a service using a base URL and expected endpoints
export const camerasDashboardService = createApi({
  reducerPath: 'camerasDashboardApi',
  baseQuery: fetchBaseQuery({ baseUrl: process.env.REACT_APP_DEVICE_SERVICE_URL }),
  endpoints: (builder) => ({
    fetchConfigs: builder.mutation<Array<dashboardCameraConfigs> , requestConfigsInfo>({
      query: (requestCamsInfo) => ({
        url: 'camerasDashboardService.php',
        method: 'POST',
        dataType: 'JSON',
        withcredentials: true,
        body: {...requestCamsInfo, actionOption:"fetchConfigs", userId: parseInt(sessionStorage.getItem("userId") as string)}
       }),
       transformResponse: (rawResponse: Array<{ 
          idvideoDashboard: number,
          configJsonFetch: string,
          idOwnerUser: number 
        }>) => {
          const result =  rawResponse.map((config) => {
            return {...config, configJsonFetch: JSON.parse(config.configJsonFetch) as configCameraData}
          })
          return result
        }
      }),
      deleteById: builder.mutation<void , dashboardCameraConfigs>({
        query: (requestCamsInfo) => ({
          url: 'camerasDashboardService.php',
          method: 'POST',
          dataType: 'JSON',
          withcredentials: true,
          body: {...requestCamsInfo, actionOption:"deleteById", userId: parseInt(sessionStorage.getItem("userId") as string)}
        })
      }),
      saveVideoDashboard: builder.mutation<void , dashboardCameraConfigs>({
        query: (requestCamsInfo) => ({
          url: 'camerasDashboardService.php',
          method: 'POST',
          dataType: 'JSON',
          withcredentials: true,
          body: {...requestCamsInfo, actionOption:"saveVideoDashboard", configJsonFetch: JSON.stringify(requestCamsInfo.configJsonFetch), userId: parseInt(sessionStorage.getItem("userId") as string)}
        })
      })
  })
})

// Export hooks for usage in functional components, which are
// auto-generated based on the defined endpoints
export const { useFetchConfigsMutation, useDeleteByIdMutation, useSaveVideoDashboardMutation } = camerasDashboardService