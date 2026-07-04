/**
 * V10 · Sprint 3 · Share Link API hooks
 *
 * 4 端点：create / delete / latest / stats
 */
import { useMutation, useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api-client';

export const SHARE_LINK_RETRY_DELAY_MS = 100;

export const ShareLinkCreateInputSchema = z.object({
  planId: z.string().min(1),
  expiresIn: z.union([z.literal(7), z.literal(30), z.literal('forever')]),
});

export const ShareLinkResponseSchema = z.object({
  id: z.string().optional(),
  code: z.string(),
  url: z.string().url().optional(),
  share_url: z.string().url().optional(),
  planId: z.string().optional(),
  target_id: z.string().optional(),
  createdAt: z.string().optional(),
  expiresAt: z.string().nullable().optional(),
  expires_at_iso: z.string().nullable().optional(),
  revoked: z.boolean().optional(),
}).transform((value) => ({
  id: value.id ?? value.code,
  code: value.code,
  url: value.url ?? value.share_url ?? '',
  planId: value.planId ?? value.target_id ?? '',
  createdAt: value.createdAt ?? new Date().toISOString(),
  expiresAt: value.expiresAt ?? value.expires_at_iso ?? null,
  revoked: value.revoked ?? false,
}));

export const ShareLinkStatsResponseSchema = z.object({
  views: z.number().int().nonnegative().optional(),
  uniqueVisitors: z.number().int().nonnegative().optional(),
  lastAccessedAt: z.string().nullable().optional(),
  access_count: z.number().int().nonnegative().optional(),
  unique_visitors: z.number().int().nonnegative().optional(),
  last_access_at_iso: z.string().nullable().optional(),
}).transform((value) => ({
  views: value.views ?? value.access_count ?? 0,
  uniqueVisitors: value.uniqueVisitors ?? value.unique_visitors ?? 0,
  lastAccessedAt: value.lastAccessedAt ?? value.last_access_at_iso ?? null,
}));

export const ShareLinkLatestResponseSchema = ShareLinkResponseSchema.nullable();

export type ShareLinkCreateInput = z.infer<typeof ShareLinkCreateInputSchema>;
export type ShareLinkResponse = z.infer<typeof ShareLinkResponseSchema>;
export type ShareLinkStatsResponse = z.infer<typeof ShareLinkStatsResponseSchema>;

export const shareLinkKeys = {
  all: ['share-link'] as const,
  latest: () => [...shareLinkKeys.all, 'latest'] as const,
  stats: (code: string) => [...shareLinkKeys.all, 'stats', code] as const,
};

function isRetryableShareLinkError(error: Error): boolean {
  const status = (error as { status?: unknown }).status;
  if (typeof status !== 'number') return true;
  return status === 408 || status === 429 || status >= 500;
}

function retryShareLinkOnce(failureCount: number, error: Error): boolean {
  return failureCount < 1 && isRetryableShareLinkError(error);
}

export function useShareLinkCreate() {
  return useMutation<ShareLinkResponse, Error, ShareLinkCreateInput>({
    mutationFn: (input) =>
      apiClient.post<ShareLinkResponse, Record<string, unknown>>(
        '/share-link',
        {
          result_type: 'review_result',
          target_token: input.planId,
          permission: 'read',
          ttl_days: input.expiresIn === 'forever' ? undefined : input.expiresIn,
          replace_existing: true,
        },
        ShareLinkResponseSchema,
      ),
    retry: retryShareLinkOnce,
    retryDelay: SHARE_LINK_RETRY_DELAY_MS,
  });
}

export function useShareLinkDelete() {
  return useMutation<{ success: boolean }, Error, string>({
    mutationFn: async (code) => {
      const res = await apiClient.post<{ revoked: boolean; changed: boolean }, Record<string, never>>(
        `/share-link/${code}/revoke`,
        {},
        z.object({ revoked: z.boolean(), changed: z.boolean() }),
      );
      return { success: res.revoked };
    },
    retry: retryShareLinkOnce,
    retryDelay: SHARE_LINK_RETRY_DELAY_MS,
  });
}

export function useShareLinkLatestQuery() {
  return useQuery<ShareLinkResponse | null>({
    queryKey: shareLinkKeys.latest(),
    queryFn: () => apiClient.get<ShareLinkResponse | null>('/share-link/latest', ShareLinkLatestResponseSchema),
    staleTime: 60 * 1000,
    retry: retryShareLinkOnce,
    retryDelay: SHARE_LINK_RETRY_DELAY_MS,
  });
}

export function useShareLinkStatsQuery(code: string | null) {
  return useQuery<ShareLinkStatsResponse>({
    queryKey: code ? shareLinkKeys.stats(code) : ['share-link', 'stats', 'noop'],
    queryFn: () => apiClient.get<ShareLinkStatsResponse>(`/share-link/${code}/stats`, ShareLinkStatsResponseSchema),
    enabled: Boolean(code),
    refetchInterval: 30_000,
    retry: retryShareLinkOnce,
    retryDelay: SHARE_LINK_RETRY_DELAY_MS,
  });
}
