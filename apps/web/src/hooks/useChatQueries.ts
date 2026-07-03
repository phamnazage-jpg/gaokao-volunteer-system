/**
 * V10 选项 B · useChatQueries
 * 替代原型 useChat.getHistory
 */
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api-client';
import { ChatHistoryResponseSchema, type ChatHistoryResponse } from '@/lib/api-schemas';

const ChatSessionsResponseSchema = z.object({
  sessions: z.array(z.object({ id: z.string(), title: z.string(), updatedAt: z.string() })),
});
type ChatSessionsResponse = z.infer<typeof ChatSessionsResponseSchema>;
import { chatKeys } from './useChatMutations';

export function useChatHistoryQuery(sessionId: string | null) {
  return useQuery<ChatHistoryResponse, Error>({
    queryKey: sessionId ? chatKeys.history(sessionId) : ['chat', 'history', 'noop'],
    queryFn: ({ signal }) =>
      apiClient.get<ChatHistoryResponse>(`/chat/history?sessionId=${sessionId}`, ChatHistoryResponseSchema, signal),
    enabled: Boolean(sessionId),
    staleTime: 5 * 60 * 1000, // 5 分钟
    gcTime: 30 * 60 * 1000, // 30 分钟
  });
}

export function useChatSessionsQuery() {
  return useQuery<ChatSessionsResponse, Error>({
    queryKey: chatKeys.sessions(),
    queryFn: ({ signal }) =>
      apiClient.get<ChatSessionsResponse>(
        '/chat/sessions',
        ChatSessionsResponseSchema,
        signal,
      ),
    staleTime: 60 * 1000,
  });
}