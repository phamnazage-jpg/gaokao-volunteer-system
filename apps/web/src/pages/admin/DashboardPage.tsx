import { useIntl } from 'react-intl';
import { DataTable, type DataTableColumn } from '@/components/shared/DataTable';
import { LineMetricChart } from '@/components/shared/Charts';

interface RecentOrder {
  id: string;
  studentKey: string;
  provinceKey: string;
  statusKey: string;
  amount: number;
}

const stats = [
  { labelKey: 'admin.dashboard.stats.totalOrders', value: '1,248', hintKey: 'admin.dashboard.stats.totalOrdersHint' },
  { labelKey: 'admin.dashboard.stats.pendingReview', value: '36', hintKey: 'admin.dashboard.stats.pendingReviewHint' },
  { labelKey: 'admin.dashboard.stats.totalUsers', value: '8,902', hintKey: 'admin.dashboard.stats.totalUsersHint' },
  { labelKey: 'admin.dashboard.stats.totalShares', value: '2,416', hintKey: 'admin.dashboard.stats.totalSharesHint' },
] as const;

const trendData = [
  { labelKey: 'admin.dashboard.days.monday', value: 18 },
  { labelKey: 'admin.dashboard.days.tuesday', value: 24 },
  { labelKey: 'admin.dashboard.days.wednesday', value: 32 },
  { labelKey: 'admin.dashboard.days.thursday', value: 28 },
  { labelKey: 'admin.dashboard.days.friday', value: 41 },
  { labelKey: 'admin.dashboard.days.saturday', value: 37 },
  { labelKey: 'admin.dashboard.days.sunday', value: 45 },
];

const recentOrders: RecentOrder[] = [
  {
    id: 'GKO-2401',
    studentKey: 'admin.dashboard.orders.studentLi',
    provinceKey: 'admin.dashboard.orders.provinceGuangdong',
    statusKey: 'admin.dashboard.orders.statusPending',
    amount: 1299,
  },
  {
    id: 'GKO-2402',
    studentKey: 'admin.dashboard.orders.studentZhang',
    provinceKey: 'admin.dashboard.orders.provinceZhejiang',
    statusKey: 'admin.dashboard.orders.statusCompleted',
    amount: 999,
  },
  {
    id: 'GKO-2403',
    studentKey: 'admin.dashboard.orders.studentWang',
    provinceKey: 'admin.dashboard.orders.provinceJiangsu',
    statusKey: 'admin.dashboard.orders.statusNeedsRevision',
    amount: 1599,
  },
];

export function AdminDashboardPage() {
  const intl = useIntl();
  const chartData = trendData.map((item) => ({
    label: intl.formatMessage({ id: item.labelKey }),
    value: item.value,
  }));
  const columns: DataTableColumn<RecentOrder>[] = [
    { key: 'id', header: intl.formatMessage({ id: 'admin.dashboard.columns.orderId' }), accessor: (row) => row.id, sortable: true },
    { key: 'student', header: intl.formatMessage({ id: 'admin.dashboard.columns.student' }), accessor: (row) => intl.formatMessage({ id: row.studentKey }) },
    { key: 'province', header: intl.formatMessage({ id: 'admin.dashboard.columns.province' }), accessor: (row) => intl.formatMessage({ id: row.provinceKey }) },
    { key: 'status', header: intl.formatMessage({ id: 'admin.dashboard.columns.status' }), accessor: (row) => intl.formatMessage({ id: row.statusKey }), sortable: true },
    { key: 'amount', header: intl.formatMessage({ id: 'admin.dashboard.columns.amount' }), accessor: (row) => `¥${row.amount}`, align: 'right' },
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
        {stats.map((item) => (
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
          <span className="text-xs text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.dashboard.mockApiNote' })}</span>
        </div>
        <DataTable data={recentOrders} columns={columns} getRowKey={(row) => row.id} caption={intl.formatMessage({ id: 'admin.dashboard.tableCaption' })} />
      </section>
    </div>
  );
}
