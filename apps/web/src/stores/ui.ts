/**
 * V10 option B · useUIStore (Zustand 4 slice).
 * UI state for theme, sidebar, modal, and upload bar collapse.
 *
 * V10 invariants:
 *  - D2 three-theme switching (light/dark/system) + 1.2s easing via --duration-theme in globals.css.
 *  - L2 mobile 48px bottom tab.
 */
import { create } from 'zustand';
import { devtools, persist, createJSONStorage } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type { AppLocale } from '@/i18n/messages';

export type ThemePreference = 'light' | 'dark' | 'system';

export interface UIState {
  theme: ThemePreference;
  resolvedTheme: 'light' | 'dark';
  locale: AppLocale;
  sidebarOpen: boolean;
  uploadBarCollapsed: boolean;
  activeModal: string | null;
  // actions
  setTheme: (pref: ThemePreference) => void;
  setResolvedTheme: (resolved: 'light' | 'dark') => void;
  setLocale: (locale: AppLocale) => void;
  toggleSidebar: () => void;
  setSidebar: (open: boolean) => void;
  toggleUploadBar: () => void;
  setActiveModal: (id: string | null) => void;
  reset: () => void;
}

const initialState: Pick<UIState, 'theme' | 'resolvedTheme' | 'locale' | 'sidebarOpen' | 'uploadBarCollapsed' | 'activeModal'> = {
  theme: 'system',
  resolvedTheme: 'light',
  locale: 'zh-CN',
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
        setLocale: (locale) =>
          set((s) => {
            s.locale = locale;
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
        partialize: (s) => ({ theme: s.theme, locale: s.locale, uploadBarCollapsed: s.uploadBarCollapsed }),
      },
    ),
    { name: 'ui-store' },
  ),
);
