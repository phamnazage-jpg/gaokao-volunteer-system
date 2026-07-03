/**
 * V10 选项 B · useChatStore (Zustand 4 slice)
 * 替代原型 useMessages + useChat (543 行) + 6 子 hook
 *
 * 设计:
 *  - messages: Message[] (Zod discriminated union, 0 any)
 *  - isStreaming: boolean (typing 动画三态)
 *  - streamStatus: 'idle' | 'thinking' | 'paused' | 'stopped'
 *  - currentPlan: PlanCardMessageData | null
 *  - currentAuditReport: AuditReport | null
 *  - activeRecordId: string | null
 */
import { create } from 'zustand';
import { devtools, persist, createJSONStorage } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type { Message } from '@/types/message';
import type { AuditReport } from '@/types/domain';

export type StreamStatus = 'idle' | 'thinking' | 'paused' | 'stopped';

export interface ChatState {
  messages: Message[];
  isStreaming: boolean;
  streamStatus: StreamStatus;
  currentPlan: Message | null;
  currentAuditReport: AuditReport | null;
  activeRecordId: string | null;

  // actions
  appendMessage: (msg: Message) => void;
  appendUserMessage: (content: string) => string; // 返回 id
  appendAssistantMessage: (content: string) => string;
  updateLastMessage: (content: string) => void;
  clearMessages: () => void;
  setStreaming: (streaming: boolean) => void;
  setStreamStatus: (status: StreamStatus) => void;
  setCurrentPlan: (plan: Message | null) => void;
  setCurrentAuditReport: (report: AuditReport | null) => void;
  setActiveRecordId: (id: string | null) => void;
  reset: () => void;
}

const initialState: Pick<ChatState,
  'messages' | 'isStreaming' | 'streamStatus' | 'currentPlan' | 'currentAuditReport' | 'activeRecordId'
> = {
  messages: [],
  isStreaming: false,
  streamStatus: 'idle',
  currentPlan: null,
  currentAuditReport: null,
  activeRecordId: null,
};

export const useChatStore = create<ChatState>()(
  devtools(
    persist(
      immer((set) => ({
        ...initialState,
        appendMessage: (msg) =>
          set((s) => {
            s.messages.push(msg);
          }),
        appendUserMessage: (content) => {
          const id = `user-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
          set((s) => {
            s.messages.push({
              id,
              role: 'user',
              content,
              timestamp: new Date(),
            });
          });
          return id;
        },
        appendAssistantMessage: (content) => {
          const id = `assistant-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
          set((s) => {
            s.messages.push({
              id,
              role: 'assistant',
              content,
              timestamp: new Date(),
              isStreaming: true,
            });
          });
          return id;
        },
        updateLastMessage: (content) =>
          set((s) => {
            const last = s.messages.at(-1);
            if (last && last.role === 'assistant') {
              last.content = content;
              last.isStreaming = true;
            }
          }),
        clearMessages: () =>
          set((s) => {
            s.messages = [];
            s.currentPlan = null;
            s.currentAuditReport = null;
          }),
        setStreaming: (streaming) =>
          set((s) => {
            s.isStreaming = streaming;
            if (!streaming) s.streamStatus = 'idle';
          }),
        setStreamStatus: (status) =>
          set((s) => {
            s.streamStatus = status;
            s.isStreaming = status === 'thinking';
          }),
        setCurrentPlan: (plan) =>
          set((s) => {
            s.currentPlan = plan;
          }),
        setCurrentAuditReport: (report) =>
          set((s) => {
            s.currentAuditReport = report;
          }),
        setActiveRecordId: (id) =>
          set((s) => {
            s.activeRecordId = id;
          }),
        reset: () => set(() => ({ ...initialState })),
      })),
      {
        name: 'gaokao-chat-store',
        storage: createJSONStorage(() => localStorage),
        // 只持久化必要字段, 不持久化流式状态
        partialize: (s) => ({
          messages: s.messages,
          activeRecordId: s.activeRecordId,
          currentPlan: s.currentPlan,
        }),
      },
    ),
    { name: 'chat-store' },
  ),
);

// ====== Selectors (G1 闸门: 强类型, 0 any) ======

export const selectMessages = (s: ChatState) => s.messages;
export const selectIsStreaming = (s: ChatState) => s.isStreaming;
export const selectStreamStatus = (s: ChatState) => s.streamStatus;
export const selectCurrentPlan = (s: ChatState) => s.currentPlan;
export const selectActiveRecordId = (s: ChatState) => s.activeRecordId;
