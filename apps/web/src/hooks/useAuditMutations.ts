/**
 * V10 option B · useAuditMutations.
 * Replaces the legacy useAudit prototype.
 */
import { useMutation, useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api-client';
import { AuditResponseSchema, type AuditSubmitInput, type AuditResponse } from '@/lib/api-schemas';

export const auditKeys = {
  all: ['audit'] as const,
  detail: (id: string) => [...auditKeys.all, 'detail', id] as const,
  status: (id: string) => [...auditKeys.all, 'status', id] as const,
};

export function useAuditSubmitMutation() {
  return useMutation<AuditResponse, Error, AuditSubmitInput>({
    mutationFn: (input) => apiClient.post<AuditResponse, AuditSubmitInput>('/audit/submit', input, AuditResponseSchema),
  });
}

const AuditStatusSchema = z.object({
  auditId: z.string(),
  status: z.enum(['pending', 'processing', 'completed', 'failed']),
  progress: z.number().min(0).max(100).optional(),
});
export type AuditStatus = z.infer<typeof AuditStatusSchema>;

export function useAuditStatusQuery(auditId: string | null, options?: { enabled?: boolean }) {
  return useQuery<AuditStatus, Error>({
    queryKey: auditId ? auditKeys.status(auditId) : ['audit', 'status', 'noop'],
    queryFn: ({ signal }) => apiClient.get<AuditStatus>(`/audit/${auditId}/status`, AuditStatusSchema, signal),
    enabled: Boolean(auditId) && (options?.enabled ?? true),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 3000;
      if (data.status === 'completed' || data.status === 'failed') return false;
      return 3000;
    },
    staleTime: 0,
  });
}
