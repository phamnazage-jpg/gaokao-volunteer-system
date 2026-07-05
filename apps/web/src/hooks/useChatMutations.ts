/**
 * V10 option B · useChatMutations.
 * Replaces mock + fetch logic from the legacy useChat.sendMessage prototype.
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useIntl } from 'react-intl';
import { apiClient } from '@/lib/api-client';
import { readChatStream } from '@/lib/chat-stream';
import { ChatSendResponseSchema, type ChatSendInput, type ChatSendResponse } from '@/lib/api-schemas';
import { useChatStore } from '@/stores/chat';
import type { Message } from '@/types/message';

export const chatKeys = {
  all: ['chat'] as const,
  sessions: () => [...chatKeys.all, 'sessions'] as const,
  session: (id: string) => [...chatKeys.all, 'session', id] as const,
  history: (sessionId: string) => [...chatKeys.all, 'history', sessionId] as const,
};

/**
 * Send a message with the normal mutation flow and wait for the complete response.
 */
export function useChatSendMutation() {
  const intl = useIntl();
  const queryClient = useQueryClient();
  const appendUserMessage = useChatStore((s) => s.appendUserMessage);
  const appendAssistantMessage = useChatStore((s) => s.appendAssistantMessage);
  const updateLastMessage = useChatStore((s) => s.updateLastMessage);
  const setStreaming = useChatStore((s) => s.setStreaming);
  const setStreamStatus = useChatStore((s) => s.setStreamStatus);
  const setError = useChatStore((s) => s.setError);
  const sendFailedMessage = intl.formatMessage({ id: 'chat.sendFailed' });

  return useMutation<ChatSendResponse, Error, ChatSendInput>({
    mutationFn: (input) => apiClient.post<ChatSendResponse, ChatSendInput>('/chat/send', input, ChatSendResponseSchema),
    onMutate: (input) => {
      setError(null);
      appendUserMessage(input.message);
      appendAssistantMessage(intl.formatMessage({ id: 'chat.thinking' }));
      setStreaming(true);
      setStreamStatus('thinking');
    },
    onSuccess: (data) => {
      updateLastMessage(data.assistantMessage.content);
      setStreaming(false);
      setStreamStatus('idle');
      void queryClient.invalidateQueries({ queryKey: chatKeys.history(data.sessionId) });
    },
    onError: () => {
      updateLastMessage(sendFailedMessage);
      setError(sendFailedMessage);
      setStreaming(false);
      setStreamStatus('idle');
    },
  });
}

/**
 * Send a message with the SSE / NDJSON / JSON streaming flow.
 */
export function useChatStreamMutation() {
  const intl = useIntl();
  const queryClient = useQueryClient();
  const appendUserMessage = useChatStore((s) => s.appendUserMessage);
  const appendAssistantMessage = useChatStore((s) => s.appendAssistantMessage);
  const updateLastMessage = useChatStore((s) => s.updateLastMessage);
  const setStreaming = useChatStore((s) => s.setStreaming);
  const setStreamStatus = useChatStore((s) => s.setStreamStatus);
  const setError = useChatStore((s) => s.setError);
  const sendFailedMessage = intl.formatMessage({ id: 'chat.sendFailed' });

  return useMutation<Message, Error, ChatSendInput>({
    mutationFn: async (input) => {
      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { Accept: 'text/event-stream, application/x-ndjson, application/json', 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
      });
      let streamedContent = '';
      const content = await readChatStream(res, {
        onDelta: (delta) => {
          streamedContent += delta;
          updateLastMessage(streamedContent);
          setStreamStatus('thinking');
        },
        onStatus: setStreamStatus,
      });
      return {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content,
        timestamp: new Date(),
      };
    },
    onMutate: (input) => {
      setError(null);
      appendUserMessage(input.message);
      appendAssistantMessage(intl.formatMessage({ id: 'chat.thinking' }));
      setStreaming(true);
      setStreamStatus('thinking');
    },
    onSuccess: (data) => {
      updateLastMessage(data.content);
      setStreaming(false);
      setStreamStatus('idle');
    },
    onError: () => {
      updateLastMessage(sendFailedMessage);
      setError(sendFailedMessage);
      setStreaming(false);
      setStreamStatus('idle');
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: chatKeys.all });
    },
  });
}
