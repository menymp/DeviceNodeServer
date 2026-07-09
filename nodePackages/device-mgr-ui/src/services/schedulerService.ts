// src/services/schedulerService.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../store';
import { baseQueryWithReauth } from './authService';

export type SchedulerRulePayload = {
  name: string;
  enabled?: boolean;
  rule_json: any;
  safe_state?: any | null;
};

export type SchedulerRule = {
  id: number;
  name: string;
  enabled: number; // DB stores as int 0/1
  rule_json: any | null;
  safe_state: any | null;
  created_at?: string;
  updated_at?: string;
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

export const schedulerService = createApi({
  reducerPath: 'schedulerApi',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['SchedulerRules'],
  endpoints: (builder) => ({
    // GET /api/scheduler/rules?page=0&size=50
    fetchRules: builder.query<SchedulerRule[], { page?: number; size?: number } | void>({
      query: (params) => {
        const page = params?.page ?? 0;
        const size = params?.size ?? 50;
        const qp = `?page=${encodeURIComponent(String(page))}&size=${encodeURIComponent(String(size))}`;
        return { url: `/api/scheduler/rules${qp}`, method: 'GET' };
      },
      transformResponse: (raw: Array<any>) =>
        raw.map((r) => {
          const parseMaybe = (val: any) => {
            if (val === null || val === '') return null;
            if (typeof val === 'string') {
              try {
                return JSON.parse(val);
              } catch {
                // if it's a string but not valid JSON, return the raw string
                return val;
              }
            }
            // already an object/array/number/etc.
            return val;
          };

          return {
            id: r.id,
            name: r.name,
            enabled: Number(r.enabled),
            rule_json: parseMaybe(r.rule_json),
            safe_state: parseMaybe(r.safe_state),
            created_at: r.created_at,
            updated_at: r.updated_at,
          };
        }),
      providesTags: (result) =>
        result
          ? [
              ...result.map((r) => ({ type: 'SchedulerRules' as const, id: r.id })),
              { type: 'SchedulerRules', id: 'LIST' },
            ]
          : [{ type: 'SchedulerRules', id: 'LIST' }],
    }),

    // GET /api/scheduler/rules/{id}
    fetchRuleById: builder.query<SchedulerRule, { id: number }>({
      query: ({ id }) => ({ url: `/api/scheduler/rules/${id}`, method: 'GET' }),
      transformResponse: (raw: any) => {
        const parseMaybe = (val: any) => {
          if (val === null || val === '') return null;
          if (typeof val === 'string') {
            try {
              return JSON.parse(val);
            } catch {
              // If it's a string but not valid JSON, return the raw string
              return val;
            }
          }
          // already an object/array/number/etc.
          return val;
        };

        return {
          id: raw.id,
          name: raw.name,
          enabled: Number(raw.enabled),
          rule_json: parseMaybe(raw.rule_json),
          safe_state: parseMaybe(raw.safe_state),
          created_at: raw.created_at,
          updated_at: raw.updated_at,
        };
      },
      providesTags: (result) => (result ? [{ type: 'SchedulerRules' as const, id: result.id }] : []),
    }),

    // POST /api/scheduler/rules
    createRule: builder.mutation<{ id: number; name?: string }, SchedulerRulePayload>({
      query: (payload) => ({
        url: '/api/scheduler/rules',
        method: 'POST',
        body: {
          name: payload.name,
          enabled: payload.enabled ? 1 : 0,
          rule_json: payload.rule_json,
          safe_state: payload.safe_state ?? null,
        },
        headers: { 'Content-Type': 'application/json' },
      }),
      invalidatesTags: [{ type: 'SchedulerRules', id: 'LIST' }],
    }),

    // PUT /api/scheduler/rules/{id}
    updateRule: builder.mutation<{ id: number; ok?: boolean }, { id: number; payload: SchedulerRulePayload }>({
      query: ({ id, payload }) => ({
        url: `/api/scheduler/rules/${id}`,
        method: 'PUT',
        body: {
          name: payload.name,
          enabled: payload.enabled ? 1 : 0,
          rule_json: payload.rule_json,
          safe_state: payload.safe_state ?? null,
        },
        headers: { 'Content-Type': 'application/json' },
      }),
      invalidatesTags: (result, error, arg) => [{ type: 'SchedulerRules', id: arg.id }, { type: 'SchedulerRules', id: 'LIST' }],
    }),

    // DELETE /api/scheduler/rules/{id}
    deleteRule: builder.mutation<{ deleted: number }, { id: number }>({
      query: ({ id }) => ({
        url: `/api/scheduler/rules/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, arg) => [{ type: 'SchedulerRules', id: arg.id }, { type: 'SchedulerRules', id: 'LIST' }],
    }),

    // POST /api/scheduler/notify-reload
    notifyReload: builder.mutation<{ ok: boolean }, void>({
      query: () => ({
        url: '/api/scheduler/notify-reload',
        method: 'POST',
      }),
      // no cache invalidation required, but keep tag to allow refetch patterns if needed
      invalidatesTags: [{ type: 'SchedulerRules', id: 'LIST' }],
    }),
  }),
});

export const {
  useFetchRulesQuery,
  useLazyFetchRulesQuery,
  useFetchRuleByIdQuery,
  useLazyFetchRuleByIdQuery,
  useCreateRuleMutation,
  useUpdateRuleMutation,
  useDeleteRuleMutation,
  useNotifyReloadMutation,
} = schedulerService;

export default schedulerService;
