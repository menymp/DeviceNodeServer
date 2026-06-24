// src/services/camerasDashboardService.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../store';
import { baseQueryWithReauth } from './authService';

export type ConfigCameraData = {
  width?: number;
  height?: number;
  idList?: number[];
  idText?: number;
  rowLen?: number;
};

export type VideoDashboard = {
  id: number;
  config: ConfigCameraData | null;
  idOwnerUser?: number;
  created_at?: string;
};

export type CreateDashboardPayload = {
  configJsonFetch: ConfigCameraData;
};

export type UpdateDashboardPayload = {
  configJsonFetch: ConfigCameraData;
};

const baseUrl = process.env.REACT_APP_DEVICE_SERVICE_URL || '/';

const baseQuery = fetchBaseQuery({
  baseUrl,
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.accessToken;
    if (token) headers.set('Authorization', `Bearer ${token}`);
    return headers;
  },
  credentials: 'include',
});

export const camerasDashboardService = createApi({
  reducerPath: 'camerasDashboardApi',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['VideoDashboards'],
  endpoints: (builder) => ({
    // GET /api/video-dashboards
    fetchDashboards: builder.query<VideoDashboard[], void>({
      query: () => ({ url: '/api/video-dashboards', method: 'GET' }),
      transformResponse: (raw: Array<{ id: number; config: string | null; idOwnerUser?: number; created_at?: string }>) =>
        raw.map((r) => ({
          id: r.id,
          config: r.config !== null && r.config !== '' ? JSON.parse(r.config) as ConfigCameraData : null,
          idOwnerUser: r.idOwnerUser,
          created_at: r.created_at,
        })),
      providesTags: (result) =>
        result
          ? [
              ...result.map((d) => ({ type: 'VideoDashboards' as const, id: d.id })),
              { type: 'VideoDashboards', id: 'LIST' },
            ]
          : [{ type: 'VideoDashboards', id: 'LIST' }],
    }),

    // GET /api/video-dashboard/{id}
    fetchDashboardById: builder.query<VideoDashboard, { id: number }>({
      query: ({ id }) => ({ url: `/api/video-dashboard/${id}`, method: 'GET' }),
      transformResponse: (raw: { id: number; config: string | null }) => ({
        id: raw.id,
        config: raw.config !== null && raw.config !== '' ? JSON.parse(raw.config) as ConfigCameraData : null,
      }),
      providesTags: (result) => (result ? [{ type: 'VideoDashboards' as const, id: result.id }] : []),
    }),

    // POST /api/video-dashboards
    createDashboard: builder.mutation<{ id: number }, CreateDashboardPayload>({
      query: (payload) => ({
        url: '/api/video-dashboards',
        method: 'POST',
        body: { configJsonFetch: payload.configJsonFetch },
        headers: { 'Content-Type': 'application/json' },
      }),
      invalidatesTags: [{ type: 'VideoDashboards', id: 'LIST' }],
    }),

    // PUT /api/video-dashboards/{id}
    updateDashboard: builder.mutation<{ id: number; updated: boolean }, { id: number; configJsonFetch: ConfigCameraData }>({
      query: ({ id, configJsonFetch }) => ({
        url: `/api/video-dashboards/${id}`,
        method: 'PUT',
        body: { configJsonFetch },
        headers: { 'Content-Type': 'application/json' },
      }),
      invalidatesTags: (result, error, arg) => [{ type: 'VideoDashboards', id: arg.id }, { type: 'VideoDashboards', id: 'LIST' }],
    }),

    // DELETE /api/video-dashboards/{id}
    deleteDashboard: builder.mutation<{ deleted: number }, { id: number }>({
      query: ({ id }) => ({
        url: `/api/video-dashboards/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, arg) => [{ type: 'VideoDashboards', id: arg.id }, { type: 'VideoDashboards', id: 'LIST' }],
    }),
  }),
});

export const {
  useFetchDashboardsQuery,
  useLazyFetchDashboardsQuery,
  useFetchDashboardByIdQuery,
  useLazyFetchDashboardByIdQuery,
  useCreateDashboardMutation,
  useUpdateDashboardMutation,
  useDeleteDashboardMutation,
} = camerasDashboardService;

export default camerasDashboardService;
