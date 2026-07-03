/**
 * V10 选项 B · useChatMutations
 * 替代原型 useChat.sendMessage 中的 mock + fetch 逻辑
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
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
 * 发送消息 (普通 mutation, 等待完整响应)
 */
export function useChatSendMutation() {
  const queryClient = useQueryClient();
  const appendUserMessage = useChatStore((s) => s.appendUserMessage);
  const appendAssistantMessage = useChatStore((s) => s.appendAssistantMessage);
  const updateLastMessage = useChatStore((s) => s.updateLastMessage);
  const setStreaming = useChatStore((s) => s.setStreaming);
  const setStreamStatus = useChatStore((s) => s.setStreamStatus);

  return useMutation<ChatSendResponse, Error, ChatSendInput>({
    mutationFn: (input) => apiClient.post<ChatSendResponse, ChatSendInput>('/chat/send', input, ChatSendResponseSchema),
    onMutate: (input) => {
      appendUserMessage(input.message);
      appendAssistantMessage('正在思考...');
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
      setStreaming(false);
      setStreamStatus('idle');
    },
  });
}

/**
 * 发送消息 (SSE / NDJSON / JSON 流式版本)
 */
export function useChatStreamMutation() {
  const queryClient = useQueryClient();
  const appendUserMessage = useChatStore((s) => s.appendUserMessage);
  const appendAssistantMessage = useChatStore((s) => s.appendAssistantMessage);
  const updateLastMessage = useChatStore((s) => s.updateLastMessage);
  const setStreaming = useChatStore((s) => s.setStreaming);
  const setStreamStatus = useChatStore((s) => s.setStreamStatus);

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
      appendUserMessage(input.message);
      appendAssistantMessage('');
      setStreaming(true);
      setStreamStatus('thinking');
    },
    onSuccess: (data) => {
      updateLastMessage(data.content);
      setStreaming(false);
      setStreamStatus('idle');
    },
    onError: () => {
      setStreaming(false);
      setStreamStatus('idle');
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: chatKeys.all });
    },
  });
}
