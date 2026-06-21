// src/services/authService.ts
import { createApi, fetchBaseQuery, FetchArgs, FetchBaseQueryError } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../store';
import { setCredentials, clearCredentials } from '../store/authSlice';

export type LoginRequest = {
  username: string;
  password: string;
};

export type LoginResponse = {
  access_token: string;
  refresh_token: string; // not the best practice to return it in body, but for testing
  token_type: string;
  expires_in: number;
  user_id?: number;
  idUser?: number;
  userId?: number;
  username?: string;
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
export const baseQueryWithReauth = async (args: string | FetchArgs, api: any, extraOptions: any) => {
  let result = await baseQuery(args, api, extraOptions);

  // If unauthorized, attempt refresh and retry original request
  if (result.error && (result.error as FetchBaseQueryError).status === 401) {
    const refreshToken = sessionStorage.getItem("refreshToken");
    // call refresh endpoint (will include cookie because credentials: 'include')
    const refreshResult = await baseQuery(
      {
        url: '/auth/refresh',
        method: 'POST',
        body: { refresh_token: refreshToken } // during testing, this is not a good practice since it nulls the purpose of cookies and refresh long live token
      },
      api,
      extraOptions
    );

    if (refreshResult.data) {
      // refresh returned new access token
      const data = refreshResult.data as LoginResponse;
      const userId = (data as any).user_id ?? (data as any).idUser ?? (data as any).userId ?? null;
      api.dispatch(setCredentials({ accessToken: data.access_token, userId }));

      // persist to sessionStorage
      if (typeof window !== 'undefined' && window.sessionStorage) {
        window.sessionStorage.setItem('accessToken', data.access_token);
        window.sessionStorage.setItem('refreshToken', data.refresh_token);
        if (userId !== null) window.sessionStorage.setItem('userId', String(userId));
      }

      // retry original request
      result = await baseQuery(args, api, extraOptions);
    } else {
      // refresh failed -> clear credentials
      api.dispatch(clearCredentials());
      if (typeof window !== 'undefined' && window.sessionStorage) {
        window.sessionStorage.removeItem('accessToken');
        window.sessionStorage.removeItem('userId');
        window.sessionStorage.removeItem('user');
      }
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
      }),
      async onQueryStarted(arg, { dispatch, queryFulfilled }) {
        try {
          const { data } = await queryFulfilled;
          const userId = (data as any).user_id ?? (data as any).idUser ?? (data as any).userId ?? null;
          dispatch(setCredentials({ accessToken: data.access_token, userId }));
          if (typeof window !== 'undefined' && window.sessionStorage) {
            window.sessionStorage.setItem('accessToken', data.access_token);
            window.sessionStorage.setItem('refreshToken', data.refresh_token);
            if (userId !== null) window.sessionStorage.setItem('userId', String(userId));
          }
        } catch {
          // login failed — nothing to persist
        }
      },
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
          if (typeof window !== 'undefined' && window.sessionStorage) {
            window.sessionStorage.removeItem('accessToken');
            window.sessionStorage.removeItem('user');
            window.sessionStorage.removeItem('userId');
          }
          dispatch(clearCredentials());
        }
      },
    }),

    // explicit refresh endpoint (used internally by baseQueryWithReauth or can be used directly)
    refresh: builder.mutation<LoginResponse, void>({
      query: () => ({ url: '/auth/refresh', method: 'POST' }),
      async onQueryStarted(_, { dispatch, queryFulfilled }) {
        try {
          const { data } = await queryFulfilled;
          const userId = (data as any).user_id ?? (data as any).idUser ?? (data as any).userId ?? null;
          dispatch(setCredentials({ accessToken: data.access_token, userId }));
          if (typeof window !== 'undefined' && window.sessionStorage) {
            window.sessionStorage.setItem('accessToken', data.access_token);
            if (userId !== null) window.sessionStorage.setItem('userId', String(userId));
          }
        } catch {
          // refresh failed — handled by baseQueryWithReauth or caller
        }
      },
    }),
  }),
});

export const { useLoginMutation, useLogoutMutation, useRefreshMutation } = authApi;
