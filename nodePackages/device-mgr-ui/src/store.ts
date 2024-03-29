import { configureStore } from '@reduxjs/toolkit'
// Or from '@reduxjs/toolkit/query/react'
import { setupListeners } from '@reduxjs/toolkit/query'
import { userService } from './services/userService'
import { nodesService } from './services/nodesService'
import { devicesService } from './services/deviceService'
import { camerasService } from './services/camerasService'
import { camerasDashboardService } from './services/camerasDashboardService'
import { dashboardService } from './services/dashboardService'

export const store = configureStore({
  reducer: {
    // Add the generated reducer as a specific top-level slice
    [userService.reducerPath]: userService.reducer,
    [nodesService.reducerPath]: nodesService.reducer,
    [devicesService.reducerPath]: devicesService.reducer,
    [camerasService.reducerPath]: camerasService.reducer,
    [camerasDashboardService.reducerPath]: camerasDashboardService.reducer,
    [dashboardService.reducerPath]: dashboardService.reducer,
  },
  // Adding the api middleware enables caching, invalidation, polling,
  // and other useful features of `rtk-query`.
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(userService.middleware)
    .concat(nodesService.middleware)
    .concat(devicesService.middleware)
    .concat(camerasService.middleware)
    .concat(camerasDashboardService.middleware)
    .concat(dashboardService.middleware),
})

// optional, but required for refetchOnFocus/refetchOnReconnect behaviors
// see `setupListeners` docs - takes an optional callback as the 2nd arg for customization
setupListeners(store.dispatch)