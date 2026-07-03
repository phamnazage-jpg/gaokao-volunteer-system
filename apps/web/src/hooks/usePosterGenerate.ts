/**
 * V10 · Sprint 3 · Poster Generate API hook
 */
import { useMutation } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api-client';

export const PosterGenerateInputSchema = z.object({
  planId: z.string().min(1),
  template: z.enum(['classic', 'modern', 'minimal']).default('classic'),
});

export const PosterGenerateResponseSchema = z.object({
  posterUrl: z.string().url(),
  qrCode: z.string(),
  expiresAt: z.string(),
});

export type PosterGenerateInput = z.infer<typeof PosterGenerateInputSchema>;
export type PosterGenerateResponse = z.infer<typeof PosterGenerateResponseSchema>;

export function usePosterGenerateMutation() {
  return useMutation<PosterGenerateResponse, Error, PosterGenerateInput>({
    mutationFn: (input) =>
      apiClient.post<PosterGenerateResponse, PosterGenerateInput>('/poster/generate', input, PosterGenerateResponseSchema),
  });
}