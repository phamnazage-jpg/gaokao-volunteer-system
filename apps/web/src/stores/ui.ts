/**
 * V10 选项 B · useUIStore (Zustand 4 slice)
 * 主题/侧栏/模态/上传条折叠 等 UI 状态
 *
 * V10 不变量:
 *  - D2 三主题切换 (light/dark/system) + 1.2s 缓动 (在 globals.css 通过 --duration-theme 实现)
 *  - L2 移动端 48px 底部 Tab
 */
import { create } from 'zustand';
import { devtools, persist, createJSONStorage } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

export type ThemePreference = 'light' | 'dark' | 'system';

export interface UIState {
  theme: ThemePreference;
  resolvedTheme: 'light' | 'dark';
  sidebarOpen: boolean;
  uploadBarCollapsed: boolean;
  activeModal: string | null;
  // actions
  setTheme: (pref: ThemePreference) => void;
  setResolvedTheme: (resolved: 'light' | 'dark') => void;
  toggleSidebar: () => void;
  setSidebar: (open: boolean) => void;
  toggleUploadBar: () => void;
  setActiveModal: (id: string | null) => void;
  reset: () => void;
}

const initialState: Pick<UIState, 'theme' | 'resolvedTheme' | 'sidebarOpen' | 'uploadBarCollapsed' | 'activeModal'> = {
  theme: 'system',
  resolvedTheme: 'light',
  sidebarOpen: false,
  uploadBarCollapsed: true,
  activeModal: null,
};

export const useUIStore = create<UIState>()(
  devtools(
    persist(
      immer((set) => ({
        ...initialState,
        setTheme: (pref) =>
          set((s) => {
            s.theme = pref;
          }),
        setResolvedTheme: (resolved) =>
          set((s) => {
            s.resolvedTheme = resolved;
          }),
        toggleSidebar: () =>
          set((s) => {
            s.sidebarOpen = !s.sidebarOpen;
          }),
        setSidebar: (open) =>
          set((s) => {
            s.sidebarOpen = open;
          }),
        toggleUploadBar: () =>
          set((s) => {
            s.uploadBarCollapsed = !s.uploadBarCollapsed;
          }),
        setActiveModal: (id) =>
          set((s) => {
            s.activeModal = id;
          }),
        reset: () => set(() => ({ ...initialState })),
      })),
      {
        name: 'gaokao-ui-store',
        storage: createJSONStorage(() => localStorage),
        partialize: (s) => ({ theme: s.theme, uploadBarCollapsed: s.uploadBarCollapsed }),
      },
    ),
    { name: 'ui-store' },
  ),
);
