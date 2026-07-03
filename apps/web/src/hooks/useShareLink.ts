/**
 * V10 · Sprint 3 · Share Link API hooks
 *
 * 4 端点：create / delete / latest / stats
 */
import { useMutation, useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api-client';

export const ShareLinkCreateInputSchema = z.object({
  planId: z.string().min(1),
  expiresIn: z.union([z.literal(7), z.literal(30), z.literal('forever')]),
});

export const ShareLinkResponseSchema = z.object({
  id: z.string(),
  code: z.string(),
  url: z.string().url(),
  planId: z.string(),
  createdAt: z.string(),
  expiresAt: z.string().nullable(),
});

export const ShareLinkStatsResponseSchema = z.object({
  views: z.number().int().nonnegative(),
  uniqueVisitors: z.number().int().nonnegative(),
  lastAccessedAt: z.string().nullable(),
});

export const ShareLinkLatestResponseSchema = ShareLinkResponseSchema.nullable();

export type ShareLinkCreateInput = z.infer<typeof ShareLinkCreateInputSchema>;
export type ShareLinkResponse = z.infer<typeof ShareLinkResponseSchema>;
export type ShareLinkStatsResponse = z.infer<typeof ShareLinkStatsResponseSchema>;

export const shareLinkKeys = {
  all: ['share-link'] as const,
  latest: () => [...shareLinkKeys.all, 'latest'] as const,
  stats: (code: string) => [...shareLinkKeys.all, 'stats', code] as const,
};

export function useShareLinkCreate() {
  return useMutation<ShareLinkResponse, Error, ShareLinkCreateInput>({
    mutationFn: (input) => apiClient.post<ShareLinkResponse, ShareLinkCreateInput>('/share-link', input, ShareLinkResponseSchema),
  });
}

export function useShareLinkDelete() {
  return useMutation<{ success: boolean }, Error, string>({
    mutationFn: (id) => apiClient.delete<{ success: boolean }>(`/share-link/${id}`, z.object({ success: z.boolean() })),
  });
}

export function useShareLinkLatestQuery() {
  return useQuery<ShareLinkResponse | null>({
    queryKey: shareLinkKeys.latest(),
    queryFn: () => apiClient.get<ShareLinkResponse | null>('/portal/share-link/latest', ShareLinkLatestResponseSchema),
    staleTime: 60 * 1000,
  });
}

export function useShareLinkStatsQuery(code: string | null) {
  return useQuery<ShareLinkStatsResponse>({
    queryKey: code ? shareLinkKeys.stats(code) : ['share-link', 'stats', 'noop'],
    queryFn: () => apiClient.get<ShareLinkStatsResponse>(`/share-link/${code}/stats`, ShareLinkStatsResponseSchema),
    enabled: Boolean(code),
    refetchInterval: 30_000,
  });
}