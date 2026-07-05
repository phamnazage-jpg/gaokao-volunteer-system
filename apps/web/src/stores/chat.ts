/**
 * V10 option B · useChatStore (Zustand 4 slice).
 * Replaces the legacy useMessages + useChat prototype and six child hooks.
 *
 * Design:
 *  - messages: Message[] (Zod discriminated union, 0 any)
 *  - isStreaming: boolean (three-state typing animation)
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
  lastError: string | null;

  // actions
  appendMessage: (msg: Message) => void;
  appendUserMessage: (content: string) => string; // Return id.
  appendAssistantMessage: (content: string) => string;
  updateLastMessage: (content: string) => void;
  /** Append an SSE delta to the message with the specified id. */
  appendDelta: (messageId: string, delta: string) => void;
  clearMessages: () => void;
  setStreaming: (streaming: boolean) => void;
  setStreamStatus: (status: StreamStatus) => void;
  setError: (error: string | null) => void;
  setCurrentPlan: (plan: Message | null) => void;
  setCurrentAuditReport: (report: AuditReport | null) => void;
  setActiveRecordId: (id: string | null) => void;
  reset: () => void;
}

const initialState: Pick<ChatState,
  'messages' | 'isStreaming' | 'streamStatus' | 'currentPlan' | 'currentAuditReport' | 'activeRecordId' | 'lastError'
> = {
  messages: [],
  isStreaming: false,
  streamStatus: 'idle',
  currentPlan: null,
  currentAuditReport: null,
  activeRecordId: null,
  lastError: null,
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
        appendDelta: (messageId, delta) =>
          set((s) => {
            const target = s.messages.find((m) => m.id === messageId);
            if (target) {
              target.content += delta;
              target.isStreaming = true;
            }
          }),
        setError: (error) =>
          set((s) => {
            s.lastError = error;
          }),
        clearMessages: () =>
          set((s) => {
            s.messages = [];
            s.currentPlan = null;
            s.currentAuditReport = null;
            s.lastError = null;
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
        // Persist only durable fields, not transient streaming state.
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

// ====== Selectors (G1 gate: strongly typed, 0 any) ======

export const selectMessages = (s: ChatState) => s.messages;
export const selectIsStreaming = (s: ChatState) => s.isStreaming;
export const selectStreamStatus = (s: ChatState) => s.streamStatus;
export const selectCurrentPlan = (s: ChatState) => s.currentPlan;
export const selectActiveRecordId = (s: ChatState) => s.activeRecordId;
