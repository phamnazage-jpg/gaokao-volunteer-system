import { useIntl } from 'react-intl';
import type { IntlShape } from 'react-intl';
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { DataTable, type DataTableColumn } from '@/components/shared/DataTable';
import { LineMetricChart } from '@/components/shared/Charts';
import { apiClient } from '@/lib/api-client';
import { useAdminOrdersQuery, type AdminOrderSummary } from '@/hooks/useAdminOrders';

interface RecentOrder {
  id: string;
  student: string | null;
  province: string | null;
  status: string;
  amountCents: number;
}

const DashboardStatsSchema = z.object({
  summary: z.object({
    total_orders: z.number().int().nonnegative(),
    pending_orders: z.number().int().nonnegative(),
    total_users: z.number().int().nonnegative(),
    total_shares: z.number().int().nonnegative().optional(),
  }),
  trends: z.object({
    orders_7d: z.array(z.object({ date: z.string(), count: z.number().int().nonnegative() })).optional(),
    '7d': z.array(z.object({ date: z.string(), orders: z.number().int().nonnegative() })).optional(),
  }),
});

type DashboardStats = z.infer<typeof DashboardStatsSchema>;

function toRecentOrder(order: AdminOrderSummary): RecentOrder {
  return {
    id: order.id,
    student: order.candidateName,
    province: order.candidateProvince,
    status: order.status,
    amountCents: order.amountCents,
  };
}

const statusMessageIds: Record<string, string> = {
  pending: 'admin.dashboard.orderStatus.pending',
  paid: 'admin.dashboard.orderStatus.paid',
  serving: 'admin.dashboard.orderStatus.serving',
  delivered: 'admin.dashboard.orderStatus.delivered',
  completed: 'admin.dashboard.orderStatus.completed',
  refunded: 'admin.dashboard.orderStatus.refunded',
};

function statusLabel(status: string, intl: IntlShape): string {
  const id = statusMessageIds[status];
  return id ? intl.formatMessage({ id }) : status;
}

function formatCurrency(amountCents: number): string {
  return `¥${Math.round(amountCents / 100)}`;
}

function dashboardCards(stats: DashboardStats | undefined) {
  const summary = stats?.summary;
  return [
    { labelKey: 'admin.dashboard.stats.totalOrders', value: String(summary?.total_orders ?? 0), hintKey: 'admin.dashboard.stats.totalOrdersHint' },
    { labelKey: 'admin.dashboard.stats.pendingReview', value: String(summary?.pending_orders ?? 0), hintKey: 'admin.dashboard.stats.pendingReviewHint' },
    { labelKey: 'admin.dashboard.stats.totalUsers', value: String(summary?.total_users ?? 0), hintKey: 'admin.dashboard.stats.totalUsersHint' },
    { labelKey: 'admin.dashboard.stats.totalShares', value: String(summary?.total_shares ?? 0), hintKey: 'admin.dashboard.stats.totalSharesHint' },
  ];
}

function dashboardTrend(stats: DashboardStats | undefined) {
  const points = stats?.trends.orders_7d ?? stats?.trends['7d'] ?? [];
  return points.map((point) => ({
    label: point.date.slice(5),
    value: 'count' in point ? point.count : point.orders,
  }));
}

export function AdminDashboardPage() {
  const intl = useIntl();
  const ordersQuery = useAdminOrdersQuery({ limit: 3, offset: 0 });
  const statsQuery = useQuery<DashboardStats>({
    queryKey: ['admin-dashboard-stats'],
    queryFn: () => apiClient.get<DashboardStats>('/admin/stats/dashboard', DashboardStatsSchema),
    staleTime: 60 * 1000,
  });
  const recentOrders = (ordersQuery.data ?? []).slice(0, 3).map(toRecentOrder);
  const cards = dashboardCards(statsQuery.data);
  const chartData = dashboardTrend(statsQuery.data);
  const columns: DataTableColumn<RecentOrder>[] = [
    { key: 'id', header: intl.formatMessage({ id: 'admin.dashboard.columns.orderId' }), accessor: (row) => row.id, sortable: true },
    { key: 'student', header: intl.formatMessage({ id: 'admin.dashboard.columns.student' }), accessor: (row) => row.student ?? '-' },
    { key: 'province', header: intl.formatMessage({ id: 'admin.dashboard.columns.province' }), accessor: (row) => row.province ?? '-' },
    { key: 'status', header: intl.formatMessage({ id: 'admin.dashboard.columns.status' }), accessor: (row) => statusLabel(row.status, intl), sortable: true },
    { key: 'amount', header: intl.formatMessage({ id: 'admin.dashboard.columns.amount' }), accessor: (row) => formatCurrency(row.amountCents), align: 'right' },
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] bg-gradient-to-br from-blue-600 to-cyan-500 p-6 text-white shadow-xl shadow-blue-900/10">
        <p className="text-sm font-semibold text-blue-100">Dashboard</p>
        <h2 className="mt-2 text-3xl font-black tracking-tight">{intl.formatMessage({ id: 'admin.dashboard.title' })}</h2>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-blue-50">
          {intl.formatMessage({ id: 'admin.dashboard.description' })}
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label={intl.formatMessage({ id: 'admin.dashboard.stats.ariaLabel' })}>
        {cards.map((item) => (
          <article key={item.labelKey} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <p className="text-sm text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: item.labelKey })}</p>
            <p className="mt-2 text-3xl font-black text-slate-950 dark:text-white">{item.value}</p>
            <p className="mt-2 text-xs text-blue-600 dark:text-blue-300">{intl.formatMessage({ id: item.hintKey })}</p>
          </article>
        ))}
      </section>

      <LineMetricChart
        title={intl.formatMessage({ id: 'admin.dashboard.chartTitle' })}
        data={chartData}
        ariaLabel={intl.formatMessage({ id: 'admin.dashboard.chartAriaLabel' })}
      />

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-base font-bold text-slate-950 dark:text-white">{intl.formatMessage({ id: 'admin.dashboard.recentOrdersTitle' })}</h3>
          <span className="text-xs text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.dashboard.apiNote' })}</span>
        </div>
        <DataTable data={recentOrders} columns={columns} getRowKey={(row) => row.id} caption={intl.formatMessage({ id: 'admin.dashboard.tableCaption' })} />
      </section>
    </div>
  );
}
