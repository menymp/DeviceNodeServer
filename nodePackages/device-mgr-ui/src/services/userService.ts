/// src/services/userService.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../store';
import { baseQueryWithReauth } from './authService';

export type UserMe = {
  idUser: number;
  username: string;
  email?: string;
  registerdate?: string;
  telegrambotToken?: string;
  // add other fields returned by your API
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

export const userService = createApi({
  reducerPath: 'userService',
  baseQuery: baseQueryWithReauth,
  endpoints: (builder) => ({
    getMe: builder.query<UserMe, void>({
      query: () => ({ url: '/api/users/me', method: 'GET' }),
    }),
    // add other user endpoints here (create user, update profile, etc.)
  }),
});

export const { useGetMeQuery } = userService;
