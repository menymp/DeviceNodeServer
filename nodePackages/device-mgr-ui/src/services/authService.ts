// src/services/authService.ts
import { createApi, fetchBaseQuery, FetchArgs, FetchBaseQueryError } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../store';
import { setCredentials, clearCredentials } from '../store';

export type LoginRequest = {
  username: string;
  password: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

const baseUrl = process.env.REACT_APP_DEVICE_SERVICE_URL || '/';

// baseQuery with credentials included and Authorization header from store
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

// wrapper to handle 401 -> try refresh -> retry original
const baseQueryWithReauth = async (args: string | FetchArgs, api: any, extraOptions: any) => {
  let result = await baseQuery(args, api, extraOptions);

  if (result.error && (result.error as FetchBaseQueryError).status === 401) {
    // try refresh
    const refreshResult = await baseQuery(
      {
        url: '/auth/refresh',
        method: 'POST',
      },
      api,
      extraOptions
    );

    if (refreshResult.data) {
      // refresh returned new access token
      const data = refreshResult.data as LoginResponse;
      api.dispatch(setCredentials({ accessToken: data.access_token }));
      // retry original request
      result = await baseQuery(args, api, extraOptions);
    } else {
      // refresh failed -> clear credentials
      api.dispatch(clearCredentials());
    }
  }

  return result;
};

export const authApi = createApi({
  reducerPath: 'authApi',
  baseQuery: baseQueryWithReauth,
  endpoints: (builder) => ({
    login: builder.mutation<LoginResponse, LoginRequest>({
      query: (credentials) => ({
        url: '/auth/login',
        method: 'POST',
        body: credentials,
        // credentials included by baseQuery
      }),
      // on success, caller should dispatch setCredentials with returned token
    }),
    logout: builder.mutation<void, void>({
      query: () => ({
        url: '/auth/logout',
        method: 'POST',
      }),
      async onQueryStarted(_, { dispatch, queryFulfilled }) {
        try {
          await queryFulfilled;
        } finally {
          // clear local token regardless of server response
          dispatch(clearCredentials());
        }
      },
    }),
    // optional explicit refresh endpoint (used internally by baseQueryWithReauth)
    refresh: builder.mutation<LoginResponse, void>({
      query: () => ({ url: '/auth/refresh', method: 'POST' }),
    }),
  }),
});

export const { useLoginMutation, useLogoutMutation, useRefreshMutation } = authApi;
