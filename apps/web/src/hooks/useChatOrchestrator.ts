/**
 * V10 · Sprint 3 · useChatOrchestrator
 *
 * 编排 Zustand chat store + TanStack Query mutations
 */
import { useCallback, useMemo } from 'react';
import { useChatStore } from '@/stores/chat';
import { useUserStore } from '@/stores/user';
import { useChatSendMutation } from '@/hooks/useChatMutations';
import type { Message } from '@/types/message';

export interface ChatOrchestratorResult {
  readonly send: (content: string) => void;
  readonly cancel: () => void;
  readonly isStreaming: boolean;
  readonly lastError: string | null;
  readonly canSend: boolean;
  readonly messageCount: number;
}

export function useChatOrchestrator(): ChatOrchestratorResult {
  const user = useUserStore((s) => s.name);
  const messages = useChatStore((s) => s.messages);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const lastError = useChatStore((s) => s.lastError);
  const appendMessage = useChatStore((s) => s.appendMessage);
  const updateLastMessage = useChatStore((s) => s.updateLastMessage);
  const setStreaming = useChatStore((s) => s.setStreaming);
  const setError = useChatStore((s) => s.setError);
  const activeRecordId = useChatStore((s) => s.activeRecordId);

  const sendMutation = useChatSendMutation();

  const send = useCallback(
    (content: string) => {
      const trimmed = content.trim();
      if (!trimmed || isStreaming) return;
      const userMsg: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: trimmed,
        timestamp: new Date(),
      };
      appendMessage(userMsg);
      setStreaming(true);
      setError(null);
      sendMutation.mutate(
        { message: trimmed, sessionId: activeRecordId ?? '', userName: user ?? '匿名' },
        {
          onSuccess: (data) => {
            updateLastMessage(data.assistantMessage.content);
            setStreaming(false);
          },
          onError: (err: Error) => {
            setStreaming(false);
            setError(err.message || '发送失败');
          },
        },
      );
    },
    [
      isStreaming,
      appendMessage,
      setStreaming,
      setError,
      sendMutation,
      activeRecordId,
      user,
      updateLastMessage,
    ],
  );

  const cancel = useCallback(() => {
    setStreaming(false);
    setError(null);
  }, [setStreaming, setError]);

  return useMemo(
    () => ({
      send,
      cancel,
      isStreaming,
      lastError,
      canSend: !isStreaming,
      messageCount: messages.length,
    }),
    [send, cancel, isStreaming, lastError, messages.length],
  );
}