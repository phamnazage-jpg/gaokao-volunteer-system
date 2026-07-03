/**
 * V10 选项 B · usePlanQueries
 * 替代原型 usePlan
 */
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { PlanListResponseSchema, type PlanListResponse, PlanSchema, type Plan } from '@/lib/api-schemas';

export const planKeys = {
  all: ['plans'] as const,
  list: () => [...planKeys.all, 'list'] as const,
  detail: (id: string) => [...planKeys.all, 'detail', id] as const,
};

export function usePlansQuery() {
  return useQuery<PlanListResponse, Error>({
    queryKey: planKeys.list(),
    queryFn: ({ signal }) => apiClient.get<PlanListResponse>('/plans', PlanListResponseSchema, signal),
    staleTime: 60 * 1000,
  });
}

export function usePlanQuery(id: string | null) {
  return useQuery<Plan, Error>({
    queryKey: id ? planKeys.detail(id) : ['plans', 'detail', 'noop'],
    queryFn: ({ signal }) => apiClient.get<Plan>(`/plans/${id}`, PlanSchema, signal),
    enabled: Boolean(id),
    staleTime: 5 * 60 * 1000,
  });
}