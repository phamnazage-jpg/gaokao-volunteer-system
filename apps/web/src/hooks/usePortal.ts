/**
 * V10 · Sprint 3 · Portal API hooks
 */
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api-client';

export const PortalCWBResponseSchema = z.object({
  token: z.string(),
  province: z.string(),
  year: z.number().int(),
  scoreType: z.enum(['physics', 'history']),
  score: z.number(),
  rank: z.number().int(),
  equivalentScore: z.number(),
});

export const PortalFullPlanResponseSchema = z.object({
  token: z.string(),
  plan: z.object({
    id: z.string(),
    title: z.string(),
    schools: z.array(
      z.object({
        id: z.string(),
        name: z.string(),
        majors: z.array(z.string()),
        admissionProbability: z.enum(['\u51b2', '\u7a33', '\u4fdd']),
      }),
    ),
  }),
  createdAt: z.string(),
});

export type PortalCWBResponse = z.infer<typeof PortalCWBResponseSchema>;
export type PortalFullPlanResponse = z.infer<typeof PortalFullPlanResponseSchema>;

export const portalKeys = {
  all: ['portal'] as const,
  cwb: (token: string) => [...portalKeys.all, 'cwb', token] as const,
  fullPlan: (token: string) => [...portalKeys.all, 'full-plan', token] as const,
};

export function usePortalCWBQuery(token: string | null) {
  return useQuery<PortalCWBResponse>({
    queryKey: token ? portalKeys.cwb(token) : ['portal', 'cwb', 'noop'],
    queryFn: () => apiClient.get<PortalCWBResponse>(`/portal/${token}/cwb`, PortalCWBResponseSchema),
    enabled: Boolean(token),
    staleTime: 60 * 1000,
  });
}

export function usePortalFullPlanQuery(token: string | null) {
  return useQuery<PortalFullPlanResponse>({
    queryKey: token ? portalKeys.fullPlan(token) : ['portal', 'full-plan', 'noop'],
    queryFn: () => apiClient.get<PortalFullPlanResponse>(`/portal/${token}/full-plan`, PortalFullPlanResponseSchema),
    enabled: Boolean(token),
  });
}
