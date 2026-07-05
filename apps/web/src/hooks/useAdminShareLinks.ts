import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api-client';

export type AdminShareLinkStatus = 'active' | 'revoked' | 'expired';
export type AdminShareLinkResultType = 'review_result' | 'report';

export const AdminShareLinkSchema = z
  .object({
    id: z.string().optional(),
    code: z.string(),
    share_url: z.string().url().optional(),
    url: z.string().url().optional(),
    result_type: z.union([z.literal('review_result'), z.literal('report')]).optional(),
    resultType: z.union([z.literal('review_result'), z.literal('report')]).optional(),
    target_id: z.string().optional(),
    targetId: z.string().optional(),
    created_at: z.string().nullable().optional(),
    createdAt: z.string().nullable().optional(),
    expires_at_iso: z.string().nullable().optional(),
    expiresAt: z.string().nullable().optional(),
    revoked: z.boolean().optional(),
    access_count: z.number().int().nonnegative().optional(),
    views: z.number().int().nonnegative().optional(),
    unique_visitors: z.number().int().nonnegative().optional(),
    uniqueVisitors: z.number().int().nonnegative().optional(),
    last_access_at_iso: z.string().nullable().optional(),
    lastAccessedAt: z.string().nullable().optional(),
  })
  .transform((item) => {
    const expiresAt = item.expiresAt ?? item.expires_at_iso ?? null;
    const revoked = item.revoked ?? false;
    const isExpired = expiresAt ? new Date(expiresAt).getTime() <= Date.now() : false;
    const status: AdminShareLinkStatus = revoked ? 'revoked' : isExpired ? 'expired' : 'active';

    return {
      id: item.id ?? item.code,
      code: item.code,
      url: item.url ?? item.share_url ?? '',
      resultType: item.resultType ?? item.result_type ?? 'review_result',
      targetId: item.targetId ?? item.target_id ?? '',
      createdAt: item.createdAt ?? item.created_at ?? null,
      expiresAt,
      revoked,
      status,
      views: item.views ?? item.access_count ?? 0,
      uniqueVisitors: item.uniqueVisitors ?? item.unique_visitors ?? 0,
      lastAccessedAt: item.lastAccessedAt ?? item.last_access_at_iso ?? null,
    };
  });

export const AdminShareLinksResponseSchema = z
  .object({
    total: z.number().int().nonnegative(),
    limit: z.number().int().positive(),
    offset: z.number().int().nonnegative(),
    items: z.array(AdminShareLinkSchema),
  })
  .or(z.array(AdminShareLinkSchema).transform((items) => ({ total: items.length, limit: items.length || 1, offset: 0, items })));

export const AdminShareLinkStatsSchema = z
  .object({
    views: z.number().int().nonnegative().optional(),
    uniqueVisitors: z.number().int().nonnegative().optional(),
    lastAccessedAt: z.string().nullable().optional(),
    access_count: z.number().int().nonnegative().optional(),
    unique_visitors: z.number().int().nonnegative().optional(),
    last_access_at_iso: z.string().nullable().optional(),
  })
  .transform((stats) => ({
    views: stats.views ?? stats.access_count ?? 0,
    uniqueVisitors: stats.uniqueVisitors ?? stats.unique_visitors ?? 0,
    lastAccessedAt: stats.lastAccessedAt ?? stats.last_access_at_iso ?? null,
  }));

export const AdminShareLinkTrendPointSchema = z
  .object({
    date: z.string(),
    views: z.number().int().nonnegative(),
  });

export const AdminShareLinkAuditLogSchema = z
  .object({
    id: z.union([z.string(), z.number()]),
    action: z.string(),
    actor: z.string().nullable().optional(),
    created_at: z.string().nullable().optional(),
    createdAt: z.string().nullable().optional(),
    note: z.string().nullable().optional(),
  })
  .transform((item) => ({
    id: String(item.id),
    action: item.action,
    actor: item.actor ?? null,
    createdAt: item.createdAt ?? item.created_at ?? null,
    note: item.note ?? null,
  }));

export const AdminShareLinkDetailSchema = z.object({
  link: AdminShareLinkSchema,
  stats: AdminShareLinkStatsSchema,
  trend: z.array(AdminShareLinkTrendPointSchema),
  auditLogs: z.array(AdminShareLinkAuditLogSchema).optional(),
  audit_logs: z.array(AdminShareLinkAuditLogSchema).optional(),
}).transform((payload) => ({
  link: payload.link,
  stats: payload.stats,
  trend: payload.trend,
  auditLogs: payload.auditLogs ?? payload.audit_logs ?? [],
}));

export type AdminShareLink = z.infer<typeof AdminShareLinkSchema>;
export type AdminShareLinksResponse = z.infer<typeof AdminShareLinksResponseSchema>;
export type AdminShareLinkStats = z.infer<typeof AdminShareLinkStatsSchema>;
export type AdminShareLinkTrendPoint = z.infer<typeof AdminShareLinkTrendPointSchema>;
export type AdminShareLinkAuditLog = z.infer<typeof AdminShareLinkAuditLogSchema>;
export type AdminShareLinkDetail = z.infer<typeof AdminShareLinkDetailSchema>;

export interface AdminShareLinksParams {
  limit: number;
  offset: number;
  status?: AdminShareLinkStatus;
  resultType?: AdminShareLinkResultType;
}

export const adminShareLinkKeys = {
  all: ['admin-share-links'] as const,
  list: (params: AdminShareLinksParams) => [...adminShareLinkKeys.all, 'list', params] as const,
  detail: (code: string) => [...adminShareLinkKeys.all, 'detail', code] as const,
};

function toQueryString(params: AdminShareLinksParams): string {
  const search = new URLSearchParams({
    limit: String(params.limit),
    offset: String(params.offset),
  });

  if (params.status) search.set('status', params.status);
  if (params.resultType) search.set('result_type', params.resultType);

  return search.toString();
}

export function useAdminShareLinksQuery(params: AdminShareLinksParams) {
  return useQuery<AdminShareLinksResponse>({
    queryKey: adminShareLinkKeys.list(params),
    queryFn: () => apiClient.get<AdminShareLinksResponse>(`/admin/share-links?${toQueryString(params)}`, AdminShareLinksResponseSchema),
    staleTime: 60 * 1000,
  });
}

export function useAdminShareLinkDetailQuery(code: string | null) {
  return useQuery<AdminShareLinkDetail>({
    queryKey: code ? adminShareLinkKeys.detail(code) : [...adminShareLinkKeys.all, 'detail', 'noop'],
    queryFn: () => apiClient.get<AdminShareLinkDetail>(`/admin/share-links/${encodeURIComponent(code!)}`, AdminShareLinkDetailSchema),
    enabled: Boolean(code),
    staleTime: 60 * 1000,
  });
}
