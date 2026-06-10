// src/store.ts
import { configureStore, createSlice, PayloadAction } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { authApi } from './services/authService';
import { userService } from './services/userService';
import { nodesService } from './services/nodesService';
import { devicesService } from './services/deviceService';
import { camerasService } from './services/camerasService';
import { camerasDashboardService } from './services/camerasDashboardService';
import { dashboardService } from './services/dashboardService';
import { schedulerService } from './services/schedulerService';
import { rfidService } from './services/rfidService';

// Auth slice: stores access token and userId in memory
type AuthState = {
  accessToken: string | null;
  userId: number | null;
};

const loadAuthFromSession = (): AuthState => {
  if (typeof window === 'undefined' || !window.sessionStorage) {
    return { accessToken: null, userId: null };
  }

  const accessToken = window.sessionStorage.getItem('accessToken');
  const userIdRaw = window.sessionStorage.getItem('userId');
  const userId = userIdRaw ? Number(userIdRaw) : null;

  return {
    accessToken: accessToken || null,
    userId,
  };
};

const initialState: AuthState = loadAuthFromSession();

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (state, action: PayloadAction<{ accessToken: string; userId?: number | null }>) => {
      state.accessToken = action.payload.accessToken;
      if (typeof action.payload.userId !== 'undefined') state.userId = action.payload.userId ?? null;
    },
    clearCredentials: (state) => {
      state.accessToken = null;
      state.userId = null;
      if (typeof window !== 'undefined' && window.sessionStorage) {
        window.sessionStorage.removeItem('accessToken');
        window.sessionStorage.removeItem('user');
        window.sessionStorage.removeItem('userId');
      }
    },
  },
});

export const { setCredentials, clearCredentials } = authSlice.actions;

export const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
    [authApi.reducerPath]: authApi.reducer,
    [userService.reducerPath]: userService.reducer,
    [nodesService.reducerPath]: nodesService.reducer,
    [devicesService.reducerPath]: devicesService.reducer,
    [camerasService.reducerPath]: camerasService.reducer,
    [camerasDashboardService.reducerPath]: camerasDashboardService.reducer,
    [dashboardService.reducerPath]: dashboardService.reducer,
    [schedulerService.reducerPath]: schedulerService.reducer,
    [rfidService.reducerPath]: rfidService.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware()
      .concat(authApi.middleware)
      .concat(userService.middleware)
      .concat(nodesService.middleware)
      .concat(devicesService.middleware)
      .concat(camerasService.middleware)
      .concat(camerasDashboardService.middleware)
      .concat(dashboardService.middleware)
      .concat(schedulerService.middleware)
      .concat(rfidService.middleware),
});

// optional listeners for refetchOnFocus/refetchOnReconnect
setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;

