/**
 * V10 选项 B · Zustand store barrel + 统一 reset 工具
 *
 * G1 闸门:
 *  - 0 any
 *  - 测试 setup.ts 用 resetAllStores() 在每个 test 前清空
 */
export { useChatStore, selectMessages, selectIsStreaming, selectStreamStatus, selectCurrentPlan, selectActiveRecordId } from './chat';
export type { ChatState, StreamStatus } from './chat';

export { useFormStore } from './form';
export type { FormState } from './form';

export { useUIStore } from './ui';
export type { UIState, ThemePreference } from './ui';

export { useUserStore } from './user';
export type { UserState } from './user';

import { useChatStore } from './chat';
import { useFormStore } from './form';
import { useUIStore } from './ui';
import { useUserStore } from './user';

/** 测试工具: 重置所有 store 到初始状态 */
export const resetAllStores = (): void => {
  useChatStore.getState().reset();
  useFormStore.getState().resetDraft();
  useUIStore.getState().reset();
  useUserStore.getState().logout();
};
