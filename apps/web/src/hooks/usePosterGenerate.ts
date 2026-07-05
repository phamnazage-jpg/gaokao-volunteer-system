/**
 * V10 · Sprint 3 · Poster Generate API hook
 */
import { useMutation, useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api-client';

export const PosterGenerateInputSchema = z.object({
  planId: z.string().min(1),
  template: z.enum(['classic', 'modern', 'minimal']).default('classic'),
});

export const PosterGenerateResponseSchema = z.object({
  jobId: z.string().optional(),
  status: z.enum(['queued', 'processing', 'completed', 'failed']).optional(),
  progress: z.number().int().min(0).max(100).optional(),
  posterUrl: z.string().url().nullable().optional(),
  qrCode: z.string().nullable().optional(),
  expiresAt: z.string().nullable().optional(),
});

export const PosterStatusResponseSchema = z.object({
  jobId: z.string(),
  status: z.enum(['queued', 'processing', 'completed', 'failed']),
  progress: z.number().int().min(0).max(100),
  posterUrl: z.string().url().nullable().optional(),
  qrCode: z.string().nullable().optional(),
  expiresAt: z.string().nullable().optional(),
  updatedAt: z.string(),
});

export type PosterGenerateInput = z.infer<typeof PosterGenerateInputSchema>;
export type PosterGenerateResponse = z.infer<typeof PosterGenerateResponseSchema>;
export type PosterStatusResponse = z.infer<typeof PosterStatusResponseSchema>;

export const posterKeys = {
  all: ['poster'] as const,
  status: (jobId: string) => [...posterKeys.all, 'status', jobId] as const,
};

export function usePosterGenerateMutation() {
  return useMutation<PosterGenerateResponse, Error, PosterGenerateInput>({
    mutationFn: (input) =>
      apiClient.post<PosterGenerateResponse, PosterGenerateInput>('/poster/generate', input, PosterGenerateResponseSchema),
  });
}

export function usePosterStatusQuery(jobId: string | null) {
  return useQuery<PosterStatusResponse>({
    queryKey: jobId ? posterKeys.status(jobId) : [...posterKeys.all, 'status', 'noop'],
    queryFn: () => {
      if (!jobId) {
        throw new Error('poster job id is required');
      }
      return apiClient.get<PosterStatusResponse>(`/poster/${jobId}/status`, PosterStatusResponseSchema);
    },
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && (data.status === 'completed' || data.status === 'failed')) return false;
      return 2000;
    },
  });
}
