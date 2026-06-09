// src/services/rfidService.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../store';

export type UserRfid = {
  id: number;
  user_id: number;
  rfid_id: string;
  label?: string | null;
  enabled: number;
  created_at: string;
};

export type CreateUserRfid = {
  rfid_id: string;
  label?: string | null;
  enabled?: boolean;
};

export type UpdateUserRfid = {
  label?: string | null;
  enabled?: boolean;
};

export type ResolveRfidResult = {
  idUser: number;
  username: string;
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

export const rfidService = createApi({
  reducerPath: 'rfidApi',
  baseQuery,
  tagTypes: ['UserRfids'],
  endpoints: (builder) => ({
    // GET /api/users/{id}/rfids
    fetchUserRfids: builder.query<UserRfid[], { userId: number }>({
      query: ({ userId }) => ({ url: `/api/users/${userId}/rfids`, method: 'GET' }),
      providesTags: (result, error, arg) =>
        result
          ? [
              ...result.map((r) => ({ type: 'UserRfids' as const, id: r.id })),
              { type: 'UserRfids', id: `USER_${arg.userId}` },
            ]
          : [{ type: 'UserRfids', id: `USER_${arg.userId}` }],
    }),

    // POST /api/users/{id}/rfids
    createUserRfid: builder.mutation<{ id: number; rfid_id: string }, { userId: number; payload: CreateUserRfid }>({
      query: ({ userId, payload }) => ({
        url: `/api/users/${userId}/rfids`,
        method: 'POST',
        body: payload,
        headers: { 'Content-Type': 'application/json' },
      }),
      invalidatesTags: (result, error, arg) => [{ type: 'UserRfids', id: `USER_${arg.userId}` }],
    }),

    // PUT /api/users/{id}/rfids/{rfidId}
    updateUserRfid: builder.mutation<{ id: number; updated: boolean }, { userId: number; rfidId: number; payload: UpdateUserRfid }>({
      query: ({ userId, rfidId, payload }) => ({
        url: `/api/users/${userId}/rfids/${rfidId}`,
        method: 'PUT',
        body: payload,
        headers: { 'Content-Type': 'application/json' },
      }),
      invalidatesTags: (result, error, arg) => [{ type: 'UserRfids', id: arg.rfidId }, { type: 'UserRfids', id: `USER_${arg.userId}` }],
    }),

    // DELETE /api/users/{id}/rfids/{rfidId}
    deleteUserRfid: builder.mutation<{ deleted: number }, { userId: number; rfidId: number }>({
      query: ({ userId, rfidId }) => ({
        url: `/api/users/${userId}/rfids/${rfidId}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, arg) => [{ type: 'UserRfids', id: arg.rfidId }, { type: 'UserRfids', id: `USER_${arg.userId}` }],
    }),

    // POST /api/rfid/resolve
    resolveRfid: builder.mutation<ResolveRfidResult, { rfid_id: string }>({
      query: ({ rfid_id }) => ({
        url: '/api/rfid/resolve',
        method: 'POST',
        body: { rfid_id },
        headers: { 'Content-Type': 'application/json' },
      }),
    }),
  }),
});

export const {
  useFetchUserRfidsQuery,
  useLazyFetchUserRfidsQuery,
  useCreateUserRfidMutation,
  useUpdateUserRfidMutation,
  useDeleteUserRfidMutation,
  useResolveRfidMutation,
} = rfidService;

export default rfidService;
