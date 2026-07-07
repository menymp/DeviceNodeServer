import { createSlice, PayloadAction } from '@reduxjs/toolkit';

type AuthState = {
  accessToken: string | null;
  userId: number | null;
  is_admin?: boolean | null;
};

const loadAuthFromSession = (): AuthState => {
  if (typeof window === 'undefined' || !window.sessionStorage) {
    return { accessToken: null, userId: null, is_admin: null };
  }

  const accessToken = window.sessionStorage.getItem('accessToken');
  const userIdRaw = window.sessionStorage.getItem('userId');
  const userId = userIdRaw ? Number(userIdRaw) : null;
  const isAdmin = window.sessionStorage.getItem('is_admin') === 'true';

  return {
    accessToken: accessToken || null,
    userId,
    is_admin: isAdmin || null,
  };
};

const initialState: AuthState = loadAuthFromSession();

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (state, action: PayloadAction<{ accessToken: string; userId?: number | null, is_admin?: boolean }>) => {
      state.accessToken = action.payload.accessToken;
      if (typeof action.payload.userId !== 'undefined') state.userId = action.payload.userId ?? null;
      if (typeof action.payload.is_admin !== 'undefined') state.is_admin = action.payload.is_admin ?? null; 
// Check if needed to add access token here
// and if the user is admin
      if (typeof window !== 'undefined' && window.sessionStorage) {
        window.sessionStorage.setItem('accessToken', action.payload.accessToken);
        if (typeof action.payload.userId !== 'undefined' && action.payload.userId !== null) {
          window.sessionStorage.setItem('userId', String(action.payload.userId));
        }
        if (typeof action.payload.is_admin !== 'undefined') {
          window.sessionStorage.setItem('is_admin', String(action.payload.is_admin));
        }
      }
    },
    clearCredentials: (state) => {
      state.accessToken = null;
      state.userId = null;
      state.is_admin = null;
      if (typeof window !== 'undefined' && window.sessionStorage) {
        window.sessionStorage.removeItem('accessToken');
        window.sessionStorage.removeItem('user');
        window.sessionStorage.removeItem('userId');
        window.sessionStorage.removeItem('is_admin');
      }
    },
  },
});

export const { setCredentials, clearCredentials } = authSlice.actions;
export default authSlice.reducer;
