/**
 * V10 option B · useUserStore (Zustand 4 slice).
 *
 * Stores the current frontend user plus short-lived admin auth metadata returned
 * by the real FastAPI /api/auth/login endpoint.
 */
import { create } from 'zustand';
import { devtools, persist, createJSONStorage } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

export interface UserState {
  id: string | null;
  name: string | null;
  phone: string | null;
  role: 'user' | 'admin';
  isLoggedIn: boolean;
  token: string | null;
  tokenType: string | null;
  tokenExpiresAt: number | null;
  // actions
  setUser: (user: { id: string; name: string; phone: string; role?: 'user' | 'admin' }) => void;
  setAdminSession: (session: { username: string; accessToken: string; tokenType?: string; expiresIn: number }) => void;
  logout: () => void;
}

export const useUserStore = create<UserState>()(
  devtools(
    persist(
      immer((set) => ({
        id: null,
        name: null,
        phone: null,
        role: 'user',
        isLoggedIn: false,
        token: null,
        tokenType: null,
        tokenExpiresAt: null,
        setUser: (user) =>
          set((s) => {
            s.id = user.id;
            s.name = user.name;
            s.phone = user.phone;
            s.role = user.role ?? 'user';
            s.isLoggedIn = true;
          }),
        setAdminSession: (session) =>
          set((s) => {
            s.id = `admin:${session.username}`;
            s.name = session.username;
            s.phone = null;
            s.role = 'admin';
            s.isLoggedIn = true;
            s.token = session.accessToken;
            s.tokenType = session.tokenType ?? 'bearer';
            s.tokenExpiresAt = Date.now() + session.expiresIn * 1000;
          }),
        logout: () =>
          set((s) => {
            s.id = null;
            s.name = null;
            s.phone = null;
            s.role = 'user';
            s.isLoggedIn = false;
            s.token = null;
            s.tokenType = null;
            s.tokenExpiresAt = null;
          }),
      })),
      {
        name: 'gaokao-user-store',
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({
          id: state.id,
          name: state.name,
          phone: state.phone,
          role: state.role,
          isLoggedIn: state.isLoggedIn,
          token: state.token,
          tokenType: state.tokenType,
          tokenExpiresAt: state.tokenExpiresAt,
        }),
      },
    ),
    { name: 'user-store' },
  ),
);
