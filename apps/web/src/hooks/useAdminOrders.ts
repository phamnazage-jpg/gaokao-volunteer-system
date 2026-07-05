import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { schemas } from '@/schemas/api-generated';
import { apiClient } from '@/lib/api-client';

export const AdminOrderSummarySchema = schemas.OrderSummaryResponse.transform((order) => ({
  id: order.id,
  source: order.source,
  externalId: order.external_id ?? null,
  serviceVersion: order.service_version,
  status: order.status,
  amountCents: order.amount_cents,
  customerName: order.customer_name ?? null,
  customerPhone: order.customer_phone ?? null,
  customerWechat: order.customer_wechat ?? null,
  candidateName: order.candidate_name ?? null,
  candidateProvince: order.candidate_province ?? null,
  assignedConsultant: order.assigned_consultant ?? null,
  intakeStatus: order.intake_status ?? null,
  intakeSubmittedAt: order.intake_submitted_at ?? null,
  createdAt: order.created_at ?? null,
  statusUpdatedAt: order.status_updated_at ?? null,
  tags: order.tags ?? [],
}));

export const AdminOrdersResponseSchema = z.array(AdminOrderSummarySchema);
export const AdminOrderHistoryItemSchema = schemas.OrderHistoryItem.transform((item) => ({
  id: item.id,
  orderId: item.order_id,
  fromStatus: item.from_status ?? null,
  toStatus: item.to_status,
  actor: item.actor ?? null,
  reason: item.reason ?? null,
  changedAt: item.changed_at,
}));

export const AdminOrderDetailSchema = z
  .object({
    order: schemas.OrderSummaryResponse.extend({
      notes: z.union([z.string(), z.null()]).optional(),
      candidate_score: z.union([z.number(), z.null()]).optional(),
      candidate_rank: z.union([z.number(), z.null()]).optional(),
      candidate_subjects: z.array(z.string()).optional(),
    }),
    history: z.array(schemas.OrderHistoryItem),
    available_next_statuses: z.array(z.string()),
  })
  .transform((payload) => ({
    order: {
      ...AdminOrderSummarySchema.parse(payload.order),
      notes: payload.order.notes ?? null,
      candidateScore: payload.order.candidate_score ?? null,
      candidateRank: payload.order.candidate_rank ?? null,
      candidateSubjects: payload.order.candidate_subjects ?? [],
    },
    history: payload.history.map((item) => AdminOrderHistoryItemSchema.parse(item)),
    availableNextStatuses: payload.available_next_statuses,
  }));

export type AdminOrderStatus = 'pending' | 'paid' | 'serving' | 'delivered' | 'completed' | 'refunded';
export type AdminOrderSource = 'xianyu' | 'wechat' | 'web' | 'school';
export type AdminOrderSummary = z.infer<typeof AdminOrderSummarySchema>;
export type AdminOrderHistoryItem = z.infer<typeof AdminOrderHistoryItemSchema>;
export type AdminOrderDetail = z.infer<typeof AdminOrderDetailSchema>;

export interface AdminOrdersParams {
  limit: number;
  offset: number;
  status?: AdminOrderStatus;
  source?: AdminOrderSource;
}

export const adminOrderKeys = {
  all: ['admin-orders'] as const,
  list: (params: AdminOrdersParams) => [...adminOrderKeys.all, 'list', params] as const,
  detail: (orderId: string) => [...adminOrderKeys.all, 'detail', orderId] as const,
};

function toQueryString(params: AdminOrdersParams): string {
  const search = new URLSearchParams({
    limit: String(params.limit),
    offset: String(params.offset),
  });

  if (params.status) search.set('status', params.status);
  if (params.source) search.set('source', params.source);

  return search.toString();
}

export function useAdminOrdersQuery(params: AdminOrdersParams) {
  return useQuery<AdminOrderSummary[]>({
    queryKey: adminOrderKeys.list(params),
    queryFn: () => apiClient.get<AdminOrderSummary[]>(`/admin/orders?${toQueryString(params)}`, AdminOrdersResponseSchema),
    staleTime: 60 * 1000,
  });
}

export function useAdminOrderQuery(orderId: string | null) {
  return useQuery<AdminOrderDetail>({
    queryKey: orderId ? adminOrderKeys.detail(orderId) : [...adminOrderKeys.all, 'detail', 'noop'],
    queryFn: () => apiClient.get<AdminOrderDetail>(`/admin/orders/${encodeURIComponent(orderId!)}`, AdminOrderDetailSchema),
    enabled: Boolean(orderId),
    staleTime: 60 * 1000,
  });
}
