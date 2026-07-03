/**
 * V10 选项 B · useConsultationMutations
 * 替代原型 useConsultation 中的 newConsultation/loadConsultation/savePlan
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api-client';
import { consultationKeys } from './useConsultationQueries';

const ConsultationCreateInputSchema = z.object({
  title: z.string().min(1).max(100).optional(),
});
export type ConsultationCreateInput = z.infer<typeof ConsultationCreateInputSchema>;

const ConsultationCreateResponseSchema = z.object({
  id: z.string(),
  title: z.string(),
  createdAt: z.string(),
});

export function useConsultationCreateMutation() {
  const queryClient = useQueryClient();
  return useMutation<z.infer<typeof ConsultationCreateResponseSchema>, Error, ConsultationCreateInput>({
    mutationFn: (input) =>
      apiClient.post<z.infer<typeof ConsultationCreateResponseSchema>, ConsultationCreateInput>(
        '/consultations',
        ConsultationCreateInputSchema.parse(input),
        ConsultationCreateResponseSchema,
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: consultationKeys.list() });
    },
  });
}

const ConsultationUpdateInputSchema = z.object({
  title: z.string().min(1).max(100).optional(),
  messages: z.array(z.unknown()).optional(),
});
export type ConsultationUpdateInput = z.infer<typeof ConsultationUpdateInputSchema>;

export function useConsultationUpdateMutation() {
  const queryClient = useQueryClient();
  return useMutation<{ success: boolean }, Error, { id: string; input: ConsultationUpdateInput }>({
    mutationFn: ({ id, input }) =>
      apiClient.patch<{ success: boolean }, ConsultationUpdateInput>(`/consultations/${id}`, ConsultationUpdateInputSchema.parse(input), z.object({ success: z.boolean() })),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: consultationKeys.list() });
      void queryClient.invalidateQueries({ queryKey: consultationKeys.detail(variables.id) });
    },
  });
}

export function useConsultationDeleteMutation() {
  const queryClient = useQueryClient();
  return useMutation<{ success: boolean }, Error, string>({
    mutationFn: (id) => apiClient.delete<{ success: boolean }>(`/consultations/${id}`, z.object({ success: z.boolean() })),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: consultationKeys.list() });
    },
  });
}