// src/store.ts
import { configureStore } from '@reduxjs/toolkit';
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
import authReducer, { setCredentials, clearCredentials } from './store/authSlice';

export { setCredentials, clearCredentials } from './store/authSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
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

