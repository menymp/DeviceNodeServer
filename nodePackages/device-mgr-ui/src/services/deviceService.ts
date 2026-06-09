// src/services/devicesService.ts
import { createApi, fetchBaseQuery, FetchArgs, FetchBaseQueryError } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../store';

export type RequestDevicesInfo = {
  pageCount?: number;
  pageSize?: number;
  deviceName?: string;
  nodeName?: string;
  idDevices?: number;
};

export type RequestDeviceByIdentifier = {
  identifier?: string | number; // numeric id or tag
  tag?: string;                 // optional explicit tag query
};

export type Device = {
  idDevices: number;
  name: string;
  mode: string;
  type: string;
  channelPath: string;
  nodeName: string;
  idMode?: number;
  idType?: number;
  idParentNode?: number;
};

export type DeviceTag = {
  id: number;
  idDevices: number;
  user_id: number;
  tag: string;
  created_at: string;
};

const baseUrl = process.env.REACT_APP_DEVICE_SERVICE_URL || '/';

// baseQuery that includes credentials and Authorization header from store
const baseQuery = fetchBaseQuery({
  baseUrl,
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.accessToken;
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    return headers;
  },
  credentials: 'include', // send cookies (refresh token) for refresh endpoint
});

// Devices API
export const devicesService = createApi({
  reducerPath: 'devicesApi',
  baseQuery,
  tagTypes: ['Devices', 'DeviceTags'],
  endpoints: (builder) => ({
    // Fetch list of devices (supports query params or POST body)
    fetchDevices: builder.query<Device[], RequestDevicesInfo | void>({
      // We use POST to support legacy clients that send body; backend accepts both.
      query: (params) => ({
        url: '/api/devices',
        method: 'POST',
        body: params ?? {},
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.map((d) => ({ type: 'Devices' as const, id: d.idDevices })),
              { type: 'Devices', id: 'LIST' },
            ]
          : [{ type: 'Devices', id: 'LIST' }],
    }),

    // Fetch single device by identifier (numeric id or tag string)
    fetchDeviceByIdentifier: builder.query<Device, RequestDeviceByIdentifier>({
      // If identifier is numeric, call /api/device/{id}; if tag provided, call /api/device?tag=...
      query: ({ identifier, tag }) => {
        if (typeof identifier !== 'undefined' && identifier !== null) {
          // numeric id or tag path
          return {
            url: `/api/device/${encodeURIComponent(String(identifier))}`,
            method: 'GET',
          };
        }
        if (typeof tag !== 'undefined' && tag !== null) {
          return {
            url: `/api/device?tag=${encodeURIComponent(String(tag))}`,
            method: 'GET',
          };
        }
        // fallback: call /api/device without params (will return 400)
        return { url: '/api/device', method: 'GET' };
      },
      providesTags: (result, error, arg) => (result ? [{ type: 'Devices', id: result.idDevices }] : []),
    }),

    // Device tags (per-user)
    listTags: builder.query<DeviceTag[], { deviceId: number }>({
      query: ({ deviceId }) => ({
        url: `/api/devices/${deviceId}/tags`,
        method: 'GET',
      }),
      providesTags: (result, error, arg) =>
        result ? result.map((t) => ({ type: 'DeviceTags' as const, id: t.id })) : [{ type: 'DeviceTags', id: 'LIST' }],
    }),

    createTag: builder.mutation<DeviceTag, { deviceId: number; tag: string }>({
      query: ({ deviceId, tag }) => ({
        url: `/api/devices/${deviceId}/tags`,
        method: 'POST',
        body: { tag },
      }),
      invalidatesTags: (result, error, arg) => [{ type: 'DeviceTags', id: 'LIST' }, { type: 'Devices', id: arg.deviceId }],
    }),

    updateTag: builder.mutation<{ id: number; tag: string }, { deviceId: number; tagId: number; tag: string }>({
      query: ({ deviceId, tagId, tag }) => ({
        url: `/api/devices/${deviceId}/tags/${tagId}`,
        method: 'PUT',
        body: { tag },
      }),
      invalidatesTags: (result, error, arg) => [{ type: 'DeviceTags', id: arg.tagId }, { type: 'Devices', id: arg.deviceId }],
    }),

    deleteTag: builder.mutation<{ deleted: number }, { deviceId: number; tagId: number }>({
      query: ({ deviceId, tagId }) => ({
        url: `/api/devices/${deviceId}/tags/${tagId}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, arg) => [{ type: 'DeviceTags', id: arg.tagId }, { type: 'Devices', id: arg.deviceId }],
    }),
  }),
});

export const {
  useFetchDevicesQuery,
  useLazyFetchDevicesQuery,
  useFetchDeviceByIdentifierQuery,
  useLazyFetchDeviceByIdentifierQuery,
  useListTagsQuery,
  useCreateTagMutation,
  useUpdateTagMutation,
  useDeleteTagMutation,
} = devicesService;

export default devicesService;
