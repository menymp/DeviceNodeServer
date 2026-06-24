// src/services/nodesService.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../store';
import { baseQueryWithReauth } from './authService';

export type RequestNodesInfo = {
  page?: number;
  size?: number;
};

export type Node = {
  idNodesTable: number;
  nodeName: string;
  nodePath: string;
  idDeviceProtocol: number;
  idOwnerUser: number;
  connectionParameters: any | null;
};

export type ProtocolInfo = {
  idsupportedProtocols: number;
  ProtocolName: string;
};

const baseUrl = process.env.REACT_APP_DEVICE_SERVICE_URL || '/';

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

export const nodesService = createApi({
  reducerPath: 'nodesApi',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['Nodes', 'Protocols'],
  endpoints: (builder) => ({
    // GET /api/nodes?page=0&size=50
    fetchNodes: builder.query<Node[], RequestNodesInfo | void>({
      query: (params) => {
        const page = params?.page ?? 0;
        const size = params?.size ?? 50;
        const qp = `?page=${encodeURIComponent(String(page))}&size=${encodeURIComponent(String(size))}`;
        return { url: `/api/nodes${qp}`, method: 'GET' };
      },
      providesTags: (result) =>
        result
          ? [
              ...result.map((n) => ({ type: 'Nodes' as const, id: n.idNodesTable })),
              { type: 'Nodes', id: 'LIST' },
            ]
          : [{ type: 'Nodes', id: 'LIST' }],
    }),

    // GET /api/node/{id}
    fetchNodeById: builder.query<Node, { id: number }>({
      query: ({ id }) => ({ url: `/api/node/${id}`, method: 'GET' }),
      providesTags: (result) => (result ? [{ type: 'Nodes', id: result.idNodesTable }] : []),
    }),

    // GET /api/nodes/configs
    fetchProtocols: builder.query<ProtocolInfo[], void>({
      query: () => ({ url: '/api/nodes/configs', method: 'GET' }),
      providesTags: (result) =>
        result ? result.map((p) => ({ type: 'Protocols' as const, id: p.idsupportedProtocols })) : [{ type: 'Protocols', id: 'LIST' }],
    }),
  }),
});

export const {
  useFetchNodesQuery,
  useLazyFetchNodesQuery,
  useFetchNodeByIdQuery,
  useLazyFetchNodeByIdQuery,
  useFetchProtocolsQuery,
  useLazyFetchProtocolsQuery,
} = nodesService;

export default nodesService;
