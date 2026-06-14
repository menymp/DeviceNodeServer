import { createSlice, PayloadAction } from '@reduxjs/toolkit';

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
export default authSlice.reducer;
