import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useIntl } from 'react-intl';
import { DataTable, type DataTableColumn } from '@/components/shared/DataTable';
import { Pagination } from '@/components/shared/Pagination';
import { Select, type SelectOption } from '@/components/shared/Select';
import {
  useAdminShareLinksQuery,
  type AdminShareLink,
  type AdminShareLinkResultType,
  type AdminShareLinkStatus,
} from '@/hooks/useAdminShareLinks';

type StatusFilter = AdminShareLinkStatus | 'all';
type ResultTypeFilter = AdminShareLinkResultType | 'all';

const PAGE_SIZE = 10;

const statusOptionKeys: Array<{ value: StatusFilter; labelKey: string }> = [
  { value: 'all', labelKey: 'admin.shareLinks.status.all' },
  { value: 'active', labelKey: 'admin.shareLinks.status.active' },
  { value: 'revoked', labelKey: 'admin.shareLinks.status.revoked' },
  { value: 'expired', labelKey: 'admin.shareLinks.status.expired' },
];

const resultTypeOptionKeys: Array<{ value: ResultTypeFilter; labelKey: string }> = [
  { value: 'all', labelKey: 'admin.shareLinks.resultType.all' },
  { value: 'review_result', labelKey: 'admin.shareLinks.resultType.reviewResult' },
  { value: 'report', labelKey: 'admin.shareLinks.resultType.report' },
];

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

export function AdminShareLinksPage() {
  const intl = useIntl();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<StatusFilter>('all');
  const [resultType, setResultType] = useState<ResultTypeFilter>('all');

  const params = useMemo(
    () => ({
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
      status: status === 'all' ? undefined : status,
      resultType: resultType === 'all' ? undefined : resultType,
    }),
    [page, resultType, status],
  );
  const shareLinksQuery = useAdminShareLinksQuery(params);
  const shareLinks = shareLinksQuery.data?.items ?? [];
  const total = shareLinksQuery.data?.total ?? shareLinks.length;
  const statusOptions: SelectOption<StatusFilter>[] = statusOptionKeys.map((item) => ({
    value: item.value,
    label: intl.formatMessage({ id: item.labelKey }),
  }));
  const resultTypeOptions: SelectOption<ResultTypeFilter>[] = resultTypeOptionKeys.map((item) => ({
    value: item.value,
    label: intl.formatMessage({ id: item.labelKey }),
  }));
  const columns: DataTableColumn<AdminShareLink>[] = [
    { key: 'code', header: intl.formatMessage({ id: 'admin.shareLinks.columns.code' }), accessor: (row) => row.code, sortable: true },
    {
      key: 'resultType',
      header: intl.formatMessage({ id: 'admin.shareLinks.columns.resultType' }),
      accessor: (row) => intl.formatMessage({ id: resultTypeLabel[row.resultType] }),
      sortable: true,
    },
    { key: 'targetId', header: intl.formatMessage({ id: 'admin.shareLinks.columns.targetId' }), accessor: (row) => row.targetId || '-' },
    {
      key: 'status',
      header: intl.formatMessage({ id: 'admin.shareLinks.columns.status' }),
      accessor: (row) => intl.formatMessage({ id: statusLabel[row.status] }),
      sortable: true,
    },
    { key: 'views', header: intl.formatMessage({ id: 'admin.shareLinks.columns.views' }), accessor: (row) => row.views, align: 'right', sortable: true },
    { key: 'uniqueVisitors', header: intl.formatMessage({ id: 'admin.shareLinks.columns.uniqueVisitors' }), accessor: (row) => row.uniqueVisitors, align: 'right', sortable: true },
    { key: 'lastAccessedAt', header: intl.formatMessage({ id: 'admin.shareLinks.columns.lastAccessedAt' }), accessor: (row) => formatDate(row.lastAccessedAt, intl.locale), sortable: true },
    { key: 'expiresAt', header: intl.formatMessage({ id: 'admin.shareLinks.columns.expiresAt' }), accessor: (row) => formatDate(row.expiresAt, intl.locale), sortable: true },
    { key: 'url', header: intl.formatMessage({ id: 'admin.shareLinks.columns.url' }), accessor: (row) => formatUrl(row.url) },
  ];

  const handleStatusChange = (value: StatusFilter): void => {
    setStatus(value);
    setPage(1);
  };

  const handleResultTypeChange = (value: ResultTypeFilter): void => {
    setResultType(value);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold text-blue-600 dark:text-blue-300">T-E-10</p>
            <h2 className="mt-1 text-2xl font-black text-slate-950 dark:text-white">{intl.formatMessage({ id: 'admin.shareLinks.title' })}</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
              {intl.formatMessage({ id: 'admin.shareLinks.description' })}
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:min-w-[28rem]">
            <Select label={intl.formatMessage({ id: 'admin.shareLinks.filters.status' })} value={status} options={statusOptions} onChange={handleStatusChange} />
            <Select label={intl.formatMessage({ id: 'admin.shareLinks.filters.resultType' })} value={resultType} options={resultTypeOptions} onChange={handleResultTypeChange} />
          </div>
        </div>
      </section>

      {shareLinksQuery.isLoading && (
        <div role="status" className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
          {intl.formatMessage({ id: 'admin.shareLinks.loading' })}
        </div>
      )}

      {shareLinksQuery.isError && (
        <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
          {intl.formatMessage({ id: 'admin.shareLinks.error' })}
        </div>
      )}

      {!shareLinksQuery.isLoading && !shareLinksQuery.isError && (
        <section aria-label={intl.formatMessage({ id: 'admin.shareLinks.tableAriaLabel' })}>
          <DataTable
            data={shareLinks}
            columns={columns}
            getRowKey={(row) => row.id}
            caption={intl.formatMessage({ id: 'admin.shareLinks.tableCaption' })}
            emptyText={intl.formatMessage({ id: 'admin.shareLinks.empty' })}
          />
          {shareLinks.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {shareLinks.map((item) => (
                <Link
                  key={item.code}
                  to={`/admin/share-links/${encodeURIComponent(item.code)}`}
                  className="inline-flex min-h-9 items-center rounded-full border border-blue-200 bg-blue-50 px-3 text-xs font-semibold text-blue-700 transition hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-blue-500/30 dark:bg-blue-500/10 dark:text-blue-200"
                >
                  {intl.formatMessage({ id: 'admin.shareLinks.viewDetail' }, { code: item.code })}
                </Link>
              ))}
            </div>
          )}
          <Pagination
            page={page}
            pageSize={PAGE_SIZE}
            totalItems={total}
            onPageChange={setPage}
            label={intl.formatMessage({ id: 'admin.shareLinks.pagination' })}
          />
        </section>
      )}
    </div>
  );
}
