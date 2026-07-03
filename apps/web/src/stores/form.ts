/**
 * V10 选项 B · useFormStore (Zustand 4 slice)
 * 替代原型 useProfile (87 行) 中的受控表单状态
 *
 * RHF 7 + Zod 是表单首选, 此 store 仅保存"对话提取的中间态"
 */
import { create } from 'zustand';
import { devtools, persist, createJSONStorage } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type { UserProfile } from '@/types/domain';

export interface FormState {
  // 当前对话提取出的 profile (与 user store 的 profile 互为冗余, 但 store 隔离更清晰)
  draft: UserProfile;
  // 缺失字段
  missingFields: ReadonlyArray<keyof UserProfile>;
  // 是否有核心信息
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
