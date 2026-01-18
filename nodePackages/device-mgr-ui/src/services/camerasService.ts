// Need to use the React-specific entry point to import createApi
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export type requestCameraInfo = {
    pageCount: number;
    pageSize: number;
}

export type newCameraRequestInfo = {
    name: string;
    sourceParameters: string; //Convert this to JSON since its a JSON based value
}

export type updateCameraRequestInfo = {
    name: string;
    sourceParameters: string; //Convert this to JSON since its a JSON based value
    idVideoSource: number;
}

export type deleteCameraRequestInfo = {
    idVideoSource: number;
}

export type camera = {
    idVideoSource: number;
    name: string;
    username: string;
    sourceParameters: string; //Convert this to JSON since its a JSON based value
}

export type sourceParameters = {
    host: string;
    port: number;
    type: number;
    width: number;
    height: number;
}

// Define a service using a base URL and expected endpoints
export const camerasService = createApi({
  reducerPath: 'cameraApi',
  baseQuery: fetchBaseQuery({ baseUrl: process.env.REACT_APP_DEVICE_SERVICE_URL }),
  endpoints: (builder) => ({
    fetchCameras: builder.mutation<Array<camera> , requestCameraInfo>({
      query: (requestCamsInfo) => ({
        url: 'camerasService.php',
        method: 'POST',
        dataType: 'JSON',
        withcredentials: true,
        body: {...requestCamsInfo, actionOption:"fetchCams", userId: parseInt(sessionStorage.getItem("userId") as string)}
      })
    }),
    AddCam: builder.mutation<void , newCameraRequestInfo>({
        query: (requestNewCamInfo) => ({
          url: 'camerasService.php',
          method: 'POST',
          dataType: 'JSON',
          withcredentials: true,
          body: {...requestNewCamInfo, actionOption:"AddCam", userId: parseInt(sessionStorage.getItem("userId") as string)}
        })
      }),
    UpdateCam: builder.mutation<void , updateCameraRequestInfo>({
        query: (requestUpdateInfo) => ({
          url: 'camerasService.php',
          method: 'POST',
          dataType: 'JSON',
          withcredentials: true,
          body: {...requestUpdateInfo, actionOption:"UpdateCam", userId: parseInt(sessionStorage.getItem("userId") as string)}
        })
      }),
    DeleteCam: builder.mutation<void , deleteCameraRequestInfo>({
        query: (requestDeleteInfo) => ({
          url: 'camerasService.php',
          method: 'POST',
          dataType: 'JSON',
          withcredentials: true,
          body: {...requestDeleteInfo, actionOption:"DelCam", userId: parseInt(sessionStorage.getItem("userId") as string)}
        })
      })
  })
})

// Export hooks for usage in functional components, which are
// auto-generated based on the defined endpoints
export const { useFetchCamerasMutation, useAddCamMutation, useUpdateCamMutation, useDeleteCamMutation  } = camerasService