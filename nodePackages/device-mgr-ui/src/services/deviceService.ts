// Need to use the React-specific entry point to import createApi
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export type requestDevicesInfo = {
    pageCount: number;
    pageSize: number;
    deviceName?: string;
    nodeName?: string;
}

export type requestDeviceById = {
  deviceId: number;
}

export type requestDevicesRecordsInfo = {
  deviceId: number;
  pageSize: number;
}

export type device = {
  idDevices: number;
  name: string;
  mode: string;
  type: string; 
  channelPath: string;
  nodeName: string;
}

// Define a service using a base URL and expected endpoints
export const devicesService = createApi({
  reducerPath: 'devicesApi',
  baseQuery: fetchBaseQuery({ baseUrl: 'http://localhost:8080/DeviceNodeServer/phpWebApp/' }),
  endpoints: (builder) => ({
    fetchDevices: builder.mutation<Array<device> , requestDevicesInfo>({
      query: (requestDeviceInfo) => ({
        url: 'devicesService.php',
        method: 'POST',
        dataType: 'JSON',
        withcredentials: true,
        body: {...requestDeviceInfo, actionOption:"fetchDevices", userId: parseInt(sessionStorage.getItem("userId") as string)}
      }),
    }),
    fetchDeviceById: builder.mutation<Array<device> , requestDeviceById>({
      query: (requestDeviceInfo) => ({
        url: 'devicesService.php',
        method: 'POST',
        dataType: 'JSON',
        withcredentials: true,
        body: {...requestDeviceInfo, actionOption:"fetchDeviceById", userId: parseInt(sessionStorage.getItem("userId") as string)}
      }),
    }),
    fetchDeviceRecords: builder.mutation<Array<device> , requestDevicesRecordsInfo>({
      query: (requestDeviceRecordsInfo) => ({
        url: 'devicesService.php',
        method: 'POST',
        dataType: 'JSON',
        withcredentials: true,
        body: {...requestDeviceRecordsInfo, actionOption:"fetchDeviceRecords", userId: parseInt(sessionStorage.getItem("userId") as string)}
      }),
    }),
  })
})

// Export hooks for usage in functional components, which are
// auto-generated based on the defined endpoints
export const { useFetchDeviceByIdMutation, useFetchDevicesMutation, useFetchDeviceRecordsMutation } = devicesService