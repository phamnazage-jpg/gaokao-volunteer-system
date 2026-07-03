/**
 * V10 选项 B · useUserStore (Zustand 4 slice)
 * 替代原型 useProfile 中的 "持久用户信息" 概念
 *
 * 实际登录用户与会话中提取的 draft profile 在 useFormStore 中分离
 */
import { create } from 'zustand';
import { devtools, persist, createJSONStorage } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

export interface UserState {
  id: string | null;
  name: string | null;
  phone: string | null;
  isLoggedIn: boolean;
  // actions
  setUser: (user: { id: string; name: string; phone: string }) => void;
  logout: () => void;
}

export const useUserStore = create<UserState>()(
  devtools(
    persist(
      immer((set) => ({
        id: null,
        name: null,
        phone: null,
        isLoggedIn: false,
        setUser: (user) =>
          set((s) => {
            s.id = user.id;
            s.name = user.name;
            s.phone = user.phone;
            s.isLoggedIn = true;
          }),
        logout: () =>
          set((s) => {
            s.id = null;
            s.name = null;
            s.phone = null;
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
