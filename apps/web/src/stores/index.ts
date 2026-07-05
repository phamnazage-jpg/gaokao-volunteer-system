/**
 * V10 option B · Zustand store barrel + unified reset utility.
 *
 * G1 gate:
 *  - 0 any.
 *  - test/setup.ts calls resetAllStores() before each test.
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

/** Test helper: reset all stores to their initial state. */
export const resetAllStores = (): void => {
  useChatStore.getState().reset();
  useFormStore.getState().resetDraft();
  useUIStore.getState().reset();
  useUserStore.getState().logout();
};
