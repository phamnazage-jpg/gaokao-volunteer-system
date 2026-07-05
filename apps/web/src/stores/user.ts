/**
 * V10 option B · useUserStore (Zustand 4 slice).
 * Replaces the persistent user information concept from the legacy useProfile prototype.
 *
 * Separates the logged-in user from the draft profile extracted during a chat session in useFormStore.
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
  // actions
  setUser: (user: { id: string; name: string; phone: string; role?: 'user' | 'admin' }) => void;
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
        setUser: (user) =>
          set((s) => {
            s.id = user.id;
            s.name = user.name;
            s.phone = user.phone;
            s.role = user.role ?? 'user';
            s.isLoggedIn = true;
          }),
        logout: () =>
          set((s) => {
            s.id = null;
            s.name = null;
            s.phone = null;
            s.role = 'user';
            s.isLoggedIn = false;
          }),
      })),
      {
        name: 'gaokao-user-store',
        storage: createJSONStorage(() => localStorage),
      },
    ),
    { name: 'user-store' },
  ),
);
