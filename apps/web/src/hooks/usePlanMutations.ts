/**
 * V10 选项 B · usePlanMutations
 * 替代原型 usePlan 中的 savePlan
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api-client';
import { PlanCreateInputSchema, PlanSchema, type PlanCreateInput, type Plan } from '@/lib/api-schemas';
import { planKeys } from './usePlanQueries';

export function usePlanCreateMutation() {
  const queryClient = useQueryClient();
  return useMutation<Plan, Error, PlanCreateInput>({
    mutationFn: (input) => apiClient.post<Plan, PlanCreateInput>('/plans', input, PlanSchema),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: planKeys.list() });
    },
  });
}

const PlanUpdateInputSchema = PlanCreateInputSchema.partial();
export type PlanUpdateInput = Partial<PlanCreateInput>;

export function usePlanUpdateMutation() {
  const queryClient = useQueryClient();
  return useMutation<Plan, Error, { id: string; input: PlanUpdateInput }>({
    mutationFn: ({ id, input }) =>
      apiClient.put<Plan, PlanUpdateInput>(`/plans/${id}`, PlanUpdateInputSchema.parse(input), PlanSchema),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: planKeys.list() });
      void queryClient.invalidateQueries({ queryKey: planKeys.detail(variables.id) });
    },
  });
}

export function usePlanDeleteMutation() {
  const queryClient = useQueryClient();
  return useMutation<{ success: boolean }, Error, string>({
    mutationFn: (id) =>
      apiClient.delete<{ success: boolean }>(`/plans/${id}`, z.object({ success: z.boolean() })),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: planKeys.list() });
    },
  });
}