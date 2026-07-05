import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { schemas } from '@/schemas/api-generated';
import { apiClient } from '@/lib/api-client';

export type AdminCaseCategory = 'success' | 'typical' | 'warning';
export type AdminCaseReviewStatus = 'pending' | 'approved' | 'rejected';

export const AdminCaseSchema = schemas.CaseDetailResponse.transform((item) => ({
  id: item.id,
  title: item.title,
  category: item.category,
  reviewStatus: item.review_status,
  reviewNote: item.review_note ?? null,
  reviewer: item.reviewer ?? null,
  reviewedAt: item.reviewed_at ?? null,
  summary: item.summary ?? null,
  content: item.content ?? null,
  tags: item.tags ?? [],
  createdAt: item.created_at ?? null,
  updatedAt: item.updated_at ?? null,
}));

export const AdminCaseListSchema = schemas.CaseListResponse.transform((payload) => ({
  total: payload.total,
  limit: payload.limit,
  offset: payload.offset,
  items: payload.items.map((item) => AdminCaseSchema.parse(item)),
}));

export type AdminCase = z.infer<typeof AdminCaseSchema>;
export type AdminCaseList = z.infer<typeof AdminCaseListSchema>;

export interface AdminCasesParams {
  limit: number;
  offset: number;
  category?: AdminCaseCategory;
  reviewStatus?: AdminCaseReviewStatus;
}

export const adminCaseKeys = {
  all: ['admin-cases'] as const,
  list: (params: AdminCasesParams) => [...adminCaseKeys.all, 'list', params] as const,
  detail: (caseId: number) => [...adminCaseKeys.all, 'detail', caseId] as const,
};

function toQueryString(params: AdminCasesParams): string {
  const search = new URLSearchParams({
    limit: String(params.limit),
    offset: String(params.offset),
  });

  if (params.category) search.set('category', params.category);
  if (params.reviewStatus) search.set('review_status', params.reviewStatus);

  return search.toString();
}

export function useAdminCasesQuery(params: AdminCasesParams) {
  return useQuery<AdminCaseList>({
    queryKey: adminCaseKeys.list(params),
    queryFn: () => apiClient.get<AdminCaseList>(`/admin/cases?${toQueryString(params)}`, AdminCaseListSchema),
    staleTime: 60 * 1000,
  });
}

export function useAdminCaseQuery(caseId: number | null) {
  return useQuery<AdminCase>({
    queryKey: caseId ? adminCaseKeys.detail(caseId) : [...adminCaseKeys.all, 'detail', 'noop'],
    queryFn: () => apiClient.get<AdminCase>(`/admin/cases/${caseId!}`, AdminCaseSchema),
    enabled: caseId !== null,
    staleTime: 60 * 1000,
  });
}
