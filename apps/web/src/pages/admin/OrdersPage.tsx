import { useMemo, useState } from 'react';
import { useIntl } from 'react-intl';
import { DataTable, type DataTableColumn } from '@/components/shared/DataTable';
import { Pagination } from '@/components/shared/Pagination';
import { Select, type SelectOption } from '@/components/shared/Select';
import {
  useAdminOrdersQuery,
  type AdminOrderSource,
  type AdminOrderStatus,
  type AdminOrderSummary,
} from '@/hooks/useAdminOrders';

type StatusFilter = AdminOrderStatus | 'all';
type SourceFilter = AdminOrderSource | 'all';

const PAGE_SIZE = 10;

const statusOptionKeys: Array<{ value: StatusFilter; labelKey: string }> = [
  { value: 'all', labelKey: 'admin.orders.status.all' },
  { value: 'pending', labelKey: 'admin.orders.status.pending' },
  { value: 'paid', labelKey: 'admin.orders.status.paid' },
  { value: 'serving', labelKey: 'admin.orders.status.serving' },
  { value: 'delivered', labelKey: 'admin.orders.status.delivered' },
  { value: 'completed', labelKey: 'admin.orders.status.completed' },
  { value: 'refunded', labelKey: 'admin.orders.status.refunded' },
];

const sourceOptionKeys: Array<{ value: SourceFilter; labelKey: string }> = [
  { value: 'all', labelKey: 'admin.orders.source.all' },
  { value: 'xianyu', labelKey: 'admin.orders.source.xianyu' },
  { value: 'wechat', labelKey: 'admin.orders.source.wechat' },
  { value: 'web', labelKey: 'admin.orders.source.web' },
  { value: 'school', labelKey: 'admin.orders.source.school' },
];

const statusLabel: Record<string, string> = {
  pending: 'admin.orders.status.pending',
  paid: 'admin.orders.status.paid',
  serving: 'admin.orders.status.serving',
  delivered: 'admin.orders.status.delivered',
  completed: 'admin.orders.status.completed',
  refunded: 'admin.orders.status.refunded',
};

const sourceLabel: Record<string, string> = {
  xianyu: 'admin.orders.source.xianyu',
  wechat: 'admin.orders.source.wechat',
  web: 'admin.orders.source.web',
  school: 'admin.orders.source.school',
};

function formatMoney(cents: number, locale: string): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(cents / 100);
}

function formatDate(value: string | null, locale: string): string {
  if (!value) return '-';
  return new Intl.DateTimeFormat(locale, {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

export function AdminOrdersPage() {
  const intl = useIntl();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<StatusFilter>('all');
  const [source, setSource] = useState<SourceFilter>('all');

  const params = useMemo(
    () => ({
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
      status: status === 'all' ? undefined : status,
      source: source === 'all' ? undefined : source,
    }),
    [page, source, status],
  );
  const ordersQuery = useAdminOrdersQuery(params);
  const orders = ordersQuery.data ?? [];
  const statusOptions: SelectOption<StatusFilter>[] = statusOptionKeys.map((item) => ({
    value: item.value,
    label: intl.formatMessage({ id: item.labelKey }),
  }));
  const sourceOptions: SelectOption<SourceFilter>[] = sourceOptionKeys.map((item) => ({
    value: item.value,
    label: intl.formatMessage({ id: item.labelKey }),
  }));
  const columns: DataTableColumn<AdminOrderSummary>[] = [
    { key: 'id', header: intl.formatMessage({ id: 'admin.orders.columns.orderId' }), accessor: (row) => row.id, sortable: true },
    {
      key: 'student',
      header: intl.formatMessage({ id: 'admin.orders.columns.student' }),
      accessor: (row) => row.candidateName ?? row.customerName ?? intl.formatMessage({ id: 'admin.orders.fallback.unfilled' }),
    },
    {
      key: 'source',
      header: intl.formatMessage({ id: 'admin.orders.columns.source' }),
      accessor: (row) => (sourceLabel[row.source] ? intl.formatMessage({ id: sourceLabel[row.source] }) : row.source),
      sortable: true,
    },
    {
      key: 'status',
      header: intl.formatMessage({ id: 'admin.orders.columns.status' }),
      accessor: (row) => (statusLabel[row.status] ? intl.formatMessage({ id: statusLabel[row.status] }) : row.status),
      sortable: true,
    },
    { key: 'province', header: intl.formatMessage({ id: 'admin.orders.columns.province' }), accessor: (row) => row.candidateProvince ?? '-' },
    {
      key: 'consultant',
      header: intl.formatMessage({ id: 'admin.orders.columns.consultant' }),
      accessor: (row) => row.assignedConsultant ?? intl.formatMessage({ id: 'admin.orders.fallback.unassigned' }),
    },
    { key: 'amount', header: intl.formatMessage({ id: 'admin.orders.columns.amount' }), accessor: (row) => formatMoney(row.amountCents, intl.locale), align: 'right', sortable: true },
    { key: 'createdAt', header: intl.formatMessage({ id: 'admin.orders.columns.createdAt' }), accessor: (row) => formatDate(row.createdAt, intl.locale), sortable: true },
  ];

  const handleStatusChange = (value: StatusFilter): void => {
    setStatus(value);
    setPage(1);
  };

  const handleSourceChange = (value: SourceFilter): void => {
    setSource(value);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold text-blue-600 dark:text-blue-300">T-E-06</p>
            <h2 className="mt-1 text-2xl font-black text-slate-950 dark:text-white">{intl.formatMessage({ id: 'admin.orders.title' })}</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
              {intl.formatMessage({ id: 'admin.orders.description' })}
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:min-w-[28rem]">
            <Select label={intl.formatMessage({ id: 'admin.orders.filters.status' })} value={status} options={statusOptions} onChange={handleStatusChange} />
            <Select label={intl.formatMessage({ id: 'admin.orders.filters.source' })} value={source} options={sourceOptions} onChange={handleSourceChange} />
          </div>
        </div>
      </section>

      {ordersQuery.isLoading && (
        <div role="status" className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
          {intl.formatMessage({ id: 'admin.orders.loading' })}
        </div>
      )}

      {ordersQuery.isError && (
        <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
          {intl.formatMessage({ id: 'admin.orders.error' })}
        </div>
      )}

      {!ordersQuery.isLoading && !ordersQuery.isError && (
        <section aria-label={intl.formatMessage({ id: 'admin.orders.tableAriaLabel' })}>
          <DataTable
            data={orders}
            columns={columns}
            getRowKey={(row) => row.id}
            caption={intl.formatMessage({ id: 'admin.orders.tableCaption' })}
            emptyText={intl.formatMessage({ id: 'admin.orders.empty' })}
          />
          <Pagination
            page={page}
            pageSize={PAGE_SIZE}
            totalItems={Math.max(orders.length, page * PAGE_SIZE + (orders.length === PAGE_SIZE ? 1 : 0))}
            onPageChange={setPage}
            label={intl.formatMessage({ id: 'admin.orders.pagination' })}
          />
        </section>
      )}
    </div>
  );
}
