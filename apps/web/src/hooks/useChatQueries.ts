/**
 * V10 option B · useChatQueries.
 * Replaces getHistory / getConsultations from the legacy useChat prototype.
 */
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api-client';
import { chatKeys } from '@/hooks/useChatMutations';

export const ChatHistoryResponseSchema = z.object({
  sessionId: z.string(),
  messages: z.array(
    z.object({
      id: z.string(),
      role: z.enum(['user', 'assistant', 'system']),
      content: z.string(),
      timestamp: z.string(),
    }),
  ),
});

export const ConsultationSchema = z.object({
  id: z.string(),
  title: z.string(),
  messageCount: z.number().int().nonnegative(),
  createdAt: z.string(),
  updatedAt: z.string(),
});

export const ConsultationListResponseSchema = z.object({
  consultations: z.array(ConsultationSchema),
  total: z.number().int(),
});

export type ChatHistoryResponse = z.infer<typeof ChatHistoryResponseSchema>;
export type ConsultationListResponse = z.infer<typeof ConsultationListResponseSchema>;

export function useChatHistoryQuery(sessionId: string | null) {
  return useQuery<ChatHistoryResponse>({
    queryKey: sessionId ? chatKeys.history(sessionId) : ['chat', 'history', 'noop'],
    queryFn: () =>
      apiClient.get<ChatHistoryResponse>(
        `/chat/history?sessionId=${encodeURIComponent(sessionId ?? '')}`,
        ChatHistoryResponseSchema,
      ),
    enabled: Boolean(sessionId),
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

export function useConsultationsQuery() {
  return useQuery<ConsultationListResponse>({
    queryKey: chatKeys.sessions(),
    queryFn: () => apiClient.get<ConsultationListResponse>('/consultations', ConsultationListResponseSchema),
    staleTime: 60 * 1000,
  });
}
