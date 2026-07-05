import { Link, useParams } from 'react-router-dom';
import { useIntl } from 'react-intl';
import { DataTable, type DataTableColumn } from '@/components/shared/DataTable';
import { useAdminOrderQuery, type AdminOrderHistoryItem } from '@/hooks/useAdminOrders';

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
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

export function AdminOrderDetailPage() {
  const intl = useIntl();
  const { orderId } = useParams();
  const orderQuery = useAdminOrderQuery(orderId ?? null);
  const detail = orderQuery.data;
  const formatStatus = (status: string): string => (statusLabel[status] ? intl.formatMessage({ id: statusLabel[status] }) : status);
  const formatSource = (source: string): string => (sourceLabel[source] ? intl.formatMessage({ id: sourceLabel[source] }) : source);
  const historyColumns: DataTableColumn<AdminOrderHistoryItem>[] = [
    { key: 'changedAt', header: intl.formatMessage({ id: 'admin.orderDetail.history.time' }), accessor: (row) => formatDate(row.changedAt, intl.locale), sortable: true },
    { key: 'from', header: intl.formatMessage({ id: 'admin.orderDetail.history.from' }), accessor: (row) => (row.fromStatus ? formatStatus(row.fromStatus) : '-') },
    { key: 'to', header: intl.formatMessage({ id: 'admin.orderDetail.history.to' }), accessor: (row) => formatStatus(row.toStatus), sortable: true },
    { key: 'actor', header: intl.formatMessage({ id: 'admin.orderDetail.history.actor' }), accessor: (row) => row.actor ?? intl.formatMessage({ id: 'admin.orderDetail.systemActor' }) },
    { key: 'reason', header: intl.formatMessage({ id: 'admin.orderDetail.history.reason' }), accessor: (row) => row.reason ?? '-' },
  ];

  if (!orderId) {
    return (
      <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
        {intl.formatMessage({ id: 'admin.orderDetail.missingId' })}
      </div>
    );
  }

  if (orderQuery.isLoading) {
    return (
      <div role="status" className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
        {intl.formatMessage({ id: 'admin.orderDetail.loading' })}
      </div>
    );
  }

  if (orderQuery.isError || !detail) {
    return (
      <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
        {intl.formatMessage({ id: 'admin.orderDetail.error' })}
      </div>
    );
  }

  const { order } = detail;

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <Link to="/admin/orders" className="text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-300">
              {intl.formatMessage({ id: 'admin.orderDetail.backToOrders' })}
            </Link>
            <p className="mt-4 text-sm font-semibold text-blue-600 dark:text-blue-300">T-E-07</p>
            <h2 className="mt-1 text-2xl font-black text-slate-950 dark:text-white">
              {intl.formatMessage({ id: 'admin.orderDetail.title' }, { id: order.id })}
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
              {formatSource(order.source)} · {order.serviceVersion} · {formatStatus(order.status)}
            </p>
          </div>
          <div className="rounded-2xl bg-blue-50 px-5 py-4 text-right dark:bg-blue-500/10">
            <p className="text-xs text-blue-700 dark:text-blue-200">{intl.formatMessage({ id: 'admin.orderDetail.amount' })}</p>
            <p className="mt-1 text-2xl font-black text-blue-700 dark:text-blue-100">{formatMoney(order.amountCents, intl.locale)}</p>
          </div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h3 className="text-base font-bold text-slate-950 dark:text-white">{intl.formatMessage({ id: 'admin.orderDetail.studentInfo' })}</h3>
          <dl className="mt-4 space-y-3 text-sm">
            <div className="flex justify-between gap-3"><dt className="text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.orderDetail.name' })}</dt><dd className="font-medium text-slate-950 dark:text-white">{order.candidateName ?? intl.formatMessage({ id: 'admin.orders.fallback.unfilled' })}</dd></div>
            <div className="flex justify-between gap-3"><dt className="text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.orderDetail.province' })}</dt><dd className="font-medium text-slate-950 dark:text-white">{order.candidateProvince ?? '-'}</dd></div>
            <div className="flex justify-between gap-3"><dt className="text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.orderDetail.score' })}</dt><dd className="font-medium text-slate-950 dark:text-white">{order.candidateScore ?? '-'}</dd></div>
            <div className="flex justify-between gap-3"><dt className="text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.orderDetail.rank' })}</dt><dd className="font-medium text-slate-950 dark:text-white">{order.candidateRank ?? '-'}</dd></div>
          </dl>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h3 className="text-base font-bold text-slate-950 dark:text-white">{intl.formatMessage({ id: 'admin.orderDetail.customerInfo' })}</h3>
          <dl className="mt-4 space-y-3 text-sm">
            <div className="flex justify-between gap-3"><dt className="text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.orderDetail.parent' })}</dt><dd className="font-medium text-slate-950 dark:text-white">{order.customerName ?? intl.formatMessage({ id: 'admin.orders.fallback.unfilled' })}</dd></div>
            <div className="flex justify-between gap-3"><dt className="text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.orderDetail.phone' })}</dt><dd className="font-medium text-slate-950 dark:text-white">{order.customerPhone ?? '-'}</dd></div>
            <div className="flex justify-between gap-3"><dt className="text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.orderDetail.wechat' })}</dt><dd className="font-medium text-slate-950 dark:text-white">{order.customerWechat ?? '-'}</dd></div>
            <div className="flex justify-between gap-3"><dt className="text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.orderDetail.consultant' })}</dt><dd className="font-medium text-slate-950 dark:text-white">{order.assignedConsultant ?? intl.formatMessage({ id: 'admin.orders.fallback.unassigned' })}</dd></div>
          </dl>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h3 className="text-base font-bold text-slate-950 dark:text-white">{intl.formatMessage({ id: 'admin.orderDetail.nextActions' })}</h3>
          <div className="mt-4 flex flex-wrap gap-2">
            {detail.availableNextStatuses.length > 0 ? (
              detail.availableNextStatuses.map((status) => (
                <button
                  key={status}
                  type="button"
                  className="rounded-xl border border-blue-200 bg-blue-50 px-3 py-2 text-sm font-medium text-blue-700 transition hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-blue-500/30 dark:bg-blue-500/10 dark:text-blue-200"
                >
                  {intl.formatMessage({ id: 'admin.orderDetail.markAs' }, { status: formatStatus(status) })}
                </button>
              ))
            ) : (
              <p className="text-sm text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.orderDetail.noActions' })}</p>
            )}
          </div>
          <p className="mt-4 text-xs leading-5 text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.orderDetail.actionNote' })}</p>
        </article>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h3 className="text-base font-bold text-slate-950 dark:text-white">{intl.formatMessage({ id: 'admin.orderDetail.notes' })}</h3>
        <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{order.notes ?? intl.formatMessage({ id: 'admin.orderDetail.noNotes' })}</p>
      </section>

      <section aria-label={intl.formatMessage({ id: 'admin.orderDetail.historyAriaLabel' })}>
        <h3 className="mb-3 text-base font-bold text-slate-950 dark:text-white">{intl.formatMessage({ id: 'admin.orderDetail.historyTitle' })}</h3>
        <DataTable
          data={detail.history}
          columns={historyColumns}
          getRowKey={(row) => String(row.id)}
          caption={intl.formatMessage({ id: 'admin.orderDetail.historyCaption' })}
          emptyText={intl.formatMessage({ id: 'admin.orderDetail.noHistory' })}
        />
      </section>
    </div>
  );
}
