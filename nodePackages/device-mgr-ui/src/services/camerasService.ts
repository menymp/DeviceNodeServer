// src/services/camerasService.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../store';

export type RequestCamerasInfo = {
  page?: number;   // 0-based
  size?: number;
};

export type Camera = {
  idVideoSource: number;
  name: string;
  username: string;
  sourceParameters: any | null;
};

const baseUrl = process.env.REACT_APP_DEVICE_SERVICE_URL || '/';

const baseQuery = fetchBaseQuery({
  baseUrl,
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.accessToken;
    if (token) headers.set('Authorization', `Bearer ${token}`);
    return headers;
  },
  credentials: 'include', // send refresh cookie for refresh endpoint
});

export const camerasService = createApi({
  reducerPath: 'camerasApi',
  baseQuery,
  tagTypes: ['Cameras'],
  endpoints: (builder) => ({
    // GET /api/cameras?pageCount=0&pageSize=50
    fetchCameras: builder.query<Camera[], RequestCamerasInfo | void>({
      query: (params) => {
        const page = params?.page ?? 0;
        const size = params?.size ?? 50;
        // backend accepts pageCount/pageSize naming; keep those query keys
        const qp = `?pageCount=${encodeURIComponent(String(page))}&pageSize=${encodeURIComponent(String(size))}`;
        return { url: `/api/cameras${qp}`, method: 'GET' };
      },
      providesTags: (result) =>
        result
          ? [
              ...result.map((c) => ({ type: 'Cameras' as const, id: c.idVideoSource })),
              { type: 'Cameras', id: 'LIST' },
            ]
          : [{ type: 'Cameras', id: 'LIST' }],
    }),

    // GET /api/camera/{id}
    fetchCameraById: builder.query<Camera, { id: number }>({
      query: ({ id }) => ({ url: `/api/camera/${id}`, method: 'GET' }),
      providesTags: (result) => (result ? [{ type: 'Cameras', id: result.idVideoSource }] : []),
    }),
  }),
});

export const {
  useFetchCamerasQuery,
  useLazyFetchCamerasQuery,
  useFetchCameraByIdQuery,
  useLazyFetchCameraByIdQuery,
} = camerasService;

export default camerasService;
