/**
 * V10 · Sprint 3 · Review Flow API hooks
 */
import { useMutation, useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api-client';

export const ReviewStartInputSchema = z.object({
  planId: z.string().min(1),
  reviewerId: z.string().optional(),
});

export const ReviewStatusResponseSchema = z.object({
  id: z.string(),
  planId: z.string(),
  status: z.enum(['pending', 'in_progress', 'approved', 'rejected', 'changes_requested']),
  reviewerId: z.string().nullable(),
  comment: z.string().nullable(),
  updatedAt: z.string(),
});

export const ReviewActionInputSchema = z.discriminatedUnion('action', [
  z.object({ action: z.literal('approve'), reviewId: z.string(), comment: z.string().optional() }),
  z.object({ action: z.literal('reject'), reviewId: z.string(), comment: z.string() }),
  z.object({ action: z.literal('request_changes'), reviewId: z.string(), comment: z.string() }),
]);

export type ReviewStartInput = z.infer<typeof ReviewStartInputSchema>;
export type ReviewStatusResponse = z.infer<typeof ReviewStatusResponseSchema>;
export type ReviewActionInput = z.infer<typeof ReviewActionInputSchema>;

export const reviewKeys = {
  all: ['review'] as const,
  status: (id: string) => [...reviewKeys.all, 'status', id] as const,
};

export function useReviewStartMutation() {
  return useMutation<ReviewStatusResponse, Error, ReviewStartInput>({
    mutationFn: (input) => apiClient.post<ReviewStatusResponse, ReviewStartInput>('/review/start', input, ReviewStatusResponseSchema),
  });
}

export function useReviewStatusQuery(id: string | null) {
  return useQuery<ReviewStatusResponse>({
    queryKey: id ? reviewKeys.status(id) : ['review', 'status', 'noop'],
    queryFn: () => apiClient.get<ReviewStatusResponse>(`/review/${id}/status`, ReviewStatusResponseSchema),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && (data.status === 'approved' || data.status === 'rejected')) return false;
      return 3000;
    },
  });
}

export function useReviewActionMutation() {
  return useMutation<ReviewStatusResponse, Error, ReviewActionInput>({
    mutationFn: (input) => apiClient.post<ReviewStatusResponse, ReviewActionInput>('/review/action', input, ReviewStatusResponseSchema),
  });
}