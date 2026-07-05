import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api-client';

export type AdminPosterStatus = 'queued' | 'processing' | 'completed' | 'failed';
export type AdminPosterTemplate = 'classic' | 'modern' | 'minimal';

export const AdminPosterSchema = z
  .object({
    id: z.string().optional(),
    jobId: z.string().optional(),
    job_id: z.string().optional(),
    planId: z.string().optional(),
    plan_id: z.string().optional(),
    template: z.enum(['classic', 'modern', 'minimal']).optional(),
    status: z.enum(['queued', 'processing', 'completed', 'failed']),
    progress: z.number().int().min(0).max(100),
    posterUrl: z.string().url().nullable().optional(),
    poster_url: z.string().url().nullable().optional(),
    qrCode: z.string().nullable().optional(),
    qr_code: z.string().nullable().optional(),
    createdAt: z.string().nullable().optional(),
    created_at: z.string().nullable().optional(),
    updatedAt: z.string().nullable().optional(),
    updated_at: z.string().nullable().optional(),
    expiresAt: z.string().nullable().optional(),
    expires_at: z.string().nullable().optional(),
  })
  .transform((poster) => ({
    id: poster.id ?? poster.jobId ?? poster.job_id ?? '',
    jobId: poster.jobId ?? poster.job_id ?? poster.id ?? '',
    planId: poster.planId ?? poster.plan_id ?? '',
    template: poster.template ?? 'classic',
    status: poster.status,
    progress: poster.progress,
    posterUrl: poster.posterUrl ?? poster.poster_url ?? null,
    qrCode: poster.qrCode ?? poster.qr_code ?? null,
    createdAt: poster.createdAt ?? poster.created_at ?? null,
    updatedAt: poster.updatedAt ?? poster.updated_at ?? null,
    expiresAt: poster.expiresAt ?? poster.expires_at ?? null,
  }));

export const AdminPostersResponseSchema = z
  .object({
    total: z.number().int().nonnegative(),
    limit: z.number().int().positive(),
    offset: z.number().int().nonnegative(),
    items: z.array(AdminPosterSchema),
  })
  .or(z.array(AdminPosterSchema).transform((items) => ({ total: items.length, limit: items.length || 1, offset: 0, items })));

export type AdminPoster = z.infer<typeof AdminPosterSchema>;
export type AdminPostersResponse = z.infer<typeof AdminPostersResponseSchema>;

export interface AdminPostersParams {
  limit: number;
  offset: number;
  status?: AdminPosterStatus;
  template?: AdminPosterTemplate;
}

export const adminPosterKeys = {
  all: ['admin-posters'] as const,
  list: (params: AdminPostersParams) => [...adminPosterKeys.all, 'list', params] as const,
};

function toQueryString(params: AdminPostersParams): string {
  const search = new URLSearchParams({
    limit: String(params.limit),
    offset: String(params.offset),
  });

  if (params.status) search.set('status', params.status);
  if (params.template) search.set('template', params.template);

  return search.toString();
}

export function useAdminPostersQuery(params: AdminPostersParams) {
  return useQuery<AdminPostersResponse>({
    queryKey: adminPosterKeys.list(params),
    queryFn: () => apiClient.get<AdminPostersResponse>(`/admin/posters?${toQueryString(params)}`, AdminPostersResponseSchema),
    staleTime: 60 * 1000,
  });
}
