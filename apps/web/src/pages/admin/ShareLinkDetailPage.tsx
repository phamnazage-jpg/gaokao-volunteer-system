import { Link, useParams } from 'react-router-dom';
import { useIntl } from 'react-intl';
import { AccessTrendChart } from '@/components/AccessTrendChart';
import { DataTable, type DataTableColumn } from '@/components/shared/DataTable';
import {
  useAdminShareLinkDetailQuery,
  type AdminShareLinkAuditLog,
  type AdminShareLinkResultType,
  type AdminShareLinkStatus,
} from '@/hooks/useAdminShareLinks';

const statusLabel: Record<AdminShareLinkStatus, string> = {
  active: 'admin.shareLinks.status.active',
  revoked: 'admin.shareLinks.status.revoked',
  expired: 'admin.shareLinks.status.expired',
};

const resultTypeLabel: Record<AdminShareLinkResultType, string> = {
  review_result: 'admin.shareLinks.resultType.reviewResult',
  report: 'admin.shareLinks.resultType.report',
};

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

function formatUrl(value: string): string {
  if (!value) return '-';
  try {
    const url = new URL(value);
    return `${url.host}${url.pathname}`;
  } catch {
    return value;
  }
}

export function AdminShareLinkDetailPage() {
  const intl = useIntl();
  const { code } = useParams();
  const detailQuery = useAdminShareLinkDetailQuery(code ?? null);
  const detail = detailQuery.data;
  const auditColumns: DataTableColumn<AdminShareLinkAuditLog>[] = [
    { key: 'time', header: intl.formatMessage({ id: 'admin.shareLinkDetail.audit.time' }), accessor: (row) => formatDate(row.createdAt, intl.locale), sortable: true },
    { key: 'action', header: intl.formatMessage({ id: 'admin.shareLinkDetail.audit.action' }), accessor: (row) => row.action, sortable: true },
    { key: 'actor', header: intl.formatMessage({ id: 'admin.shareLinkDetail.audit.actor' }), accessor: (row) => row.actor ?? intl.formatMessage({ id: 'admin.shareLinkDetail.systemActor' }) },
    { key: 'note', header: intl.formatMessage({ id: 'admin.shareLinkDetail.audit.note' }), accessor: (row) => row.note ?? '-' },
  ];

  if (!code) {
    return (
      <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
        {intl.formatMessage({ id: 'admin.shareLinkDetail.missingCode' })}
      </div>
    );
  }

  if (detailQuery.isLoading) {
    return (
      <div role="status" className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
        {intl.formatMessage({ id: 'admin.shareLinkDetail.loading' })}
      </div>
    );
  }

  if (detailQuery.isError || !detail) {
    return (
      <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
        {intl.formatMessage({ id: 'admin.shareLinkDetail.error' })}
      </div>
    );
  }

  const { link, stats, trend, auditLogs } = detail;

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <Link to="/admin/share-links" className="text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-300">
          {intl.formatMessage({ id: 'admin.shareLinkDetail.backToList' })}
        </Link>
        <p className="mt-4 text-sm font-semibold text-blue-600 dark:text-blue-300">T-E-11</p>
        <h2 className="mt-1 text-3xl font-black leading-tight text-slate-950 dark:text-white">
          {intl.formatMessage({ id: 'admin.shareLinkDetail.title' }, { code: link.code })}
        </h2>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-500 dark:text-slate-400">
          {intl.formatMessage({ id: resultTypeLabel[link.resultType] })} / {intl.formatMessage({ id: statusLabel[link.status] })} / {formatUrl(link.url)}
        </p>
      </section>

      <section aria-label={intl.formatMessage({ id: 'admin.shareLinkDetail.basicInfo' })} className="grid gap-4 lg:grid-cols-4">
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <p className="text-xs text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.shareLinks.columns.targetId' })}</p>
          <p className="mt-2 text-lg font-bold text-slate-950 dark:text-white">{link.targetId || '-'}</p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <p className="text-xs text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.shareLinks.columns.createdAt' })}</p>
          <p className="mt-2 text-lg font-bold text-slate-950 dark:text-white">{formatDate(link.createdAt, intl.locale)}</p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <p className="text-xs text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.shareLinks.columns.expiresAt' })}</p>
          <p className="mt-2 text-lg font-bold text-slate-950 dark:text-white">{formatDate(link.expiresAt, intl.locale)}</p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <p className="text-xs text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.shareLinks.columns.url' })}</p>
          <p className="mt-2 break-all text-sm font-bold text-slate-950 dark:text-white">{formatUrl(link.url)}</p>
        </article>
      </section>

      <section aria-label={intl.formatMessage({ id: 'admin.shareLinkDetail.stats' })} className="grid gap-4 lg:grid-cols-3">
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <p className="text-xs text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.shareLinks.columns.views' })}</p>
          <p className="mt-2 text-3xl font-black text-slate-950 dark:text-white">{stats.views}</p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <p className="text-xs text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.shareLinks.columns.uniqueVisitors' })}</p>
          <p className="mt-2 text-3xl font-black text-slate-950 dark:text-white">{stats.uniqueVisitors}</p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <p className="text-xs text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.shareLinks.columns.lastAccessedAt' })}</p>
          <p className="mt-2 text-lg font-bold text-slate-950 dark:text-white">{formatDate(stats.lastAccessedAt, intl.locale)}</p>
        </article>
      </section>

      <AccessTrendChart data={trend} />

      <section aria-label={intl.formatMessage({ id: 'admin.shareLinkDetail.auditAriaLabel' })}>
        <h3 className="mb-3 text-base font-bold text-slate-950 dark:text-white">{intl.formatMessage({ id: 'admin.shareLinkDetail.auditTitle' })}</h3>
        <DataTable
          data={auditLogs}
          columns={auditColumns}
          getRowKey={(row) => row.id}
          caption={intl.formatMessage({ id: 'admin.shareLinkDetail.auditCaption' })}
          emptyText={intl.formatMessage({ id: 'admin.shareLinkDetail.noAuditLogs' })}
        />
      </section>
    </div>
  );
}
