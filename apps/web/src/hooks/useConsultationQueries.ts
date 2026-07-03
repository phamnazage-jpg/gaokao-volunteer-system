/**
 * V10 选项 B · useConsultationQueries
 * 替代原型 useConsultation
 */
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api-client';
import { ConsultationListResponseSchema, type ConsultationListResponse } from '@/lib/api-schemas';

export const consultationKeys = {
  all: ['consultations'] as const,
  list: () => [...consultationKeys.all, 'list'] as const,
  detail: (id: string) => [...consultationKeys.all, 'detail', id] as const,
};

export function useConsultationsQuery() {
  return useQuery<ConsultationListResponse, Error>({
    queryKey: consultationKeys.list(),
    queryFn: ({ signal }) => apiClient.get<ConsultationListResponse>('/consultations', ConsultationListResponseSchema, signal),
    staleTime: 60 * 1000,
  });
}

const ConsultationDetailSchema = z.object({
  id: z.string(),
  title: z.string(),
  messages: z.array(
    z.object({
      id: z.string(),
      role: z.enum(['user', 'assistant', 'system']),
      content: z.string(),
      timestamp: z.string(),
    }),
  ),
  createdAt: z.string(),
  updatedAt: z.string(),
});
export type ConsultationDetail = z.infer<typeof ConsultationDetailSchema>;

export function useConsultationQuery(id: string | null) {
  return useQuery<ConsultationDetail, Error>({
    queryKey: id ? consultationKeys.detail(id) : ['consultations', 'detail', 'noop'],
    queryFn: ({ signal }) => apiClient.get<ConsultationDetail>(`/consultations/${id}`, ConsultationDetailSchema, signal),
    enabled: Boolean(id),
    staleTime: 5 * 60 * 1000,
  });
}