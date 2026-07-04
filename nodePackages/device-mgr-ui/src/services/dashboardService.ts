// src/services/dashboardService.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../store';
import { baseQueryWithReauth } from './authService';

export type RequestControlsInfo = {
  page?: number; // 0-based
  size?: number;
};

export type RequestControlByIdInfo = {
  id: number;
};

export type ControlTemplate = {
  controlTemplate: string;
};

export type ControlType = {
  id: number;
  typename: string;
  controlTemplate: string;
};

export type Control = {
  idControl: number;
  name: string;
  parameters: any | null;
  typename?: string;
  idType?: number;
  username?: string;
  controlTemplate?: string | null;
};

export type SaveControlInfo = {
  idControl?: number | null;
  Name: string;
  idType: number;
  parameters?: any | null;
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

export const dashboardService = createApi({
  reducerPath: 'dashboardApi',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['Controls', 'ControlTypes'],
  endpoints: (builder) => ({
    // GET /api/controls?page=0&size=50
    fetchControls: builder.query<Control[], RequestControlsInfo | void>({
      query: (params) => {
        const page = params?.page ?? 0;
        const size = params?.size ?? 50;
        const qp = `?page=${encodeURIComponent(String(page))}&size=${encodeURIComponent(String(size))}`;
        return { url: `/api/controls${qp}`, method: 'GET' };
      },
      providesTags: (result) =>
        result
          ? [
              ...result.map((c) => ({ type: 'Controls' as const, id: c.idControl })),
              { type: 'Controls', id: 'LIST' },
            ]
          : [{ type: 'Controls', id: 'LIST' }],
    }),

    // GET /api/control/{id}
    fetchControlById: builder.query<Control, { id: number }>({
      query: ({ id }) => ({ url: `/api/control/${id}`, method: 'GET' }),
      providesTags: (result) => (result ? [{ type: 'Controls', id: result.idControl }] : []),
    }),

    // GET /api/control-types
    fetchControlTypes: builder.query<ControlType[], void>({
      query: () => ({ url: '/api/control-types', method: 'GET' }),
      providesTags: (result) =>
        result ? result.map((t) => ({ type: 'ControlTypes' as const, id: t.id })) : [{ type: 'ControlTypes', id: 'LIST' }],
    }),

    // POST /api/controls  (create or update)
    saveControl: builder.mutation<{ id: number; name?: string }, SaveControlInfo>({
      query: (payload) => ({
        url: '/api/controls',
        method: 'POST',
        body: payload,
        headers: { 'Content-Type': 'application/json' },
      }),
      invalidatesTags: (result, error, arg): Array<{ type: 'Controls'; id: string }> => {
        return [
          { type: 'Controls' as const, id: 'LIST' },
          ...(arg.idControl ? [{ type: 'Controls' as const, id: String(arg.idControl) }] : []),
        ];
      },
    }),

    // DELETE /api/controls/{id}
    deleteControl: builder.mutation<{ deleted: number }, { id: number }>({
      query: ({ id }) => ({
        url: `/api/controls/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, arg) => [{ type: 'Controls', id: arg.id }, { type: 'Controls', id: 'LIST' }],
    }),
  }),
});

export const {
  useFetchControlsQuery,
  useLazyFetchControlsQuery,
  useFetchControlByIdQuery,
  useLazyFetchControlByIdQuery,
  useFetchControlTypesQuery,
  useLazyFetchControlTypesQuery,
  useSaveControlMutation,
  useDeleteControlMutation,
} = dashboardService;

export default dashboardService;
