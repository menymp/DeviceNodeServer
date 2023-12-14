// Need to use the React-specific entry point to import createApi
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export type loginUserInfo = {
    mailuid: string;
    pwd: string;
}

export type loginUserResult = {
  result: string
}

export type userInfo = {
    username:string;
    email:string;
    registerdate:string;
    telegrambotToken:string;
}

export type userInfoRequest = {
  username: string
}

// Define a service using a base URL and expected endpoints
export const userService = createApi({
  reducerPath: 'userApi',
  baseQuery: fetchBaseQuery({ baseUrl: 'http://localhost:8080/DeviceNodeServer/phpWebApp/' }),
  endpoints: (builder) => ({
    loginUser: builder.mutation<loginUserResult , loginUserInfo>({
      query: (usrInfo) => ({
        url: 'userService.php',
        method: 'POST',
        dataType: 'JSON',
        withcredentials: true,
        body: {...usrInfo, type:"login"}
      }),
    }),
    logoutUser: builder.mutation<void , void>({
        query: () => ({
          url: 'userService.php',
          method: 'POST',
          dataType: 'JSON',
          withcredentials: true,
          body: { type:"logout"}
        }),
    }),
    getUserInfo: builder.mutation<any , userInfoRequest>({
        query: (usrInfoReq) => ({
          url: 'userInfoService.php',
          method: 'POST',
          dataType: 'JSON',
          withcredentials: true,
          body: { type:"fetchUserInfo", username: usrInfoReq.username},
          transformResponse: (response: Array<userInfoRequest>) => {
            alert(response[0])
            return response[0] 
          }
        }),
    }),
    updateUserInfo: builder.mutation<void , userInfo>({
        query: () => ({
          url: 'userInfoService.php',
          method: 'POST',
          dataType: 'JSON',
          withcredentials: true,
          body: { type:"setUserInfo"}
        }),
    }),
  }),
})

// Export hooks for usage in functional components, which are
// auto-generated based on the defined endpoints
export const { useLoginUserMutation, useLogoutUserMutation, useGetUserInfoMutation, useUpdateUserInfoMutation } = userService