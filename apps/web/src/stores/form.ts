/**
 * V10 option B · useFormStore (Zustand 4 slice).
 * Replaces the controlled form state from the legacy useProfile prototype.
 *
 * RHF 7 + Zod remain the preferred form stack; this store only keeps chat-extracted draft state.
 */
import { create } from 'zustand';
import { devtools, persist, createJSONStorage } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type { UserProfile } from '@/types/domain';

export interface FormState {
  // Profile extracted from the current chat. It overlaps with user store profile but keeps store boundaries clear.
  draft: UserProfile;
  // Missing fields.
  missingFields: ReadonlyArray<keyof UserProfile>;
  // Whether core information exists.
  hasCoreInfo: boolean;
  hasAnyInfo: boolean;

  // actions
  updateDraft: (patch: Partial<UserProfile>) => void;
  resetDraft: () => void;
  setMissingFields: (fields: ReadonlyArray<keyof UserProfile>) => void;
}

const emptyProfile: UserProfile = {};

export const useFormStore = create<FormState>()(
  devtools(
    persist(
      immer((set) => ({
        draft: emptyProfile,
        missingFields: ['province', 'score', 'rank', 'subjects'],
        hasCoreInfo: false,
        hasAnyInfo: false,

        updateDraft: (patch) =>
          set((s) => {
            Object.assign(s.draft, patch);
            const d = s.draft;
            s.hasAnyInfo = Boolean(d.province || d.score || d.subjects);
            s.hasCoreInfo = Boolean(d.province && d.score && d.subjects);
          }),
        resetDraft: () =>
          set((s) => {
            s.draft = emptyProfile;
            s.missingFields = ['province', 'score', 'rank', 'subjects'];
            s.hasCoreInfo = false;
            s.hasAnyInfo = false;
          }),
        setMissingFields: (fields) =>
          set((s) => {
            s.missingFields = [...fields];
          }),
      })),
      {
        name: 'gaokao-form-store',
        storage: createJSONStorage(() => localStorage),
        partialize: (s) => ({ draft: s.draft }),
      },
    ),
    { name: 'form-store' },
  ),
);
