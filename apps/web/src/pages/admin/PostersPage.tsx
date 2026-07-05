import { useMemo, useState } from 'react';
import { useIntl } from 'react-intl';
import { Pagination } from '@/components/shared/Pagination';
import { Select, type SelectOption } from '@/components/shared/Select';
import {
  useAdminPostersQuery,
  type AdminPosterStatus,
  type AdminPosterTemplate,
} from '@/hooks/useAdminPosters';

type StatusFilter = AdminPosterStatus | 'all';
type TemplateFilter = AdminPosterTemplate | 'all';

const PAGE_SIZE = 9;

const statusOptionKeys: Array<{ value: StatusFilter; labelKey: string }> = [
  { value: 'all', labelKey: 'admin.posters.status.all' },
  { value: 'queued', labelKey: 'admin.posters.status.queued' },
  { value: 'processing', labelKey: 'admin.posters.status.processing' },
  { value: 'completed', labelKey: 'admin.posters.status.completed' },
  { value: 'failed', labelKey: 'admin.posters.status.failed' },
];

const templateOptionKeys: Array<{ value: TemplateFilter; labelKey: string }> = [
  { value: 'all', labelKey: 'admin.posters.template.all' },
  { value: 'classic', labelKey: 'poster.template.classic' },
  { value: 'modern', labelKey: 'poster.template.modern' },
  { value: 'minimal', labelKey: 'poster.template.minimal' },
];

const statusLabel: Record<AdminPosterStatus, string> = {
  queued: 'admin.posters.status.queued',
  processing: 'admin.posters.status.processing',
  completed: 'admin.posters.status.completed',
  failed: 'admin.posters.status.failed',
};

const statusClass: Record<AdminPosterStatus, string> = {
  queued: 'border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300',
  processing: 'border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-500/30 dark:bg-blue-500/10 dark:text-blue-200',
  completed: 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200',
  failed: 'border-red-200 bg-red-50 text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200',
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

function templateKey(template: AdminPosterTemplate): string {
  return `poster.template.${template}`;
}

export function AdminPostersPage() {
  const intl = useIntl();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<StatusFilter>('all');
  const [template, setTemplate] = useState<TemplateFilter>('all');
  const params = useMemo(
    () => ({
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
      status: status === 'all' ? undefined : status,
      template: template === 'all' ? undefined : template,
    }),
    [page, status, template],
  );
  const postersQuery = useAdminPostersQuery(params);
  const posters = postersQuery.data?.items ?? [];
  const total = postersQuery.data?.total ?? posters.length;
  const statusOptions: SelectOption<StatusFilter>[] = statusOptionKeys.map((item) => ({
    value: item.value,
    label: intl.formatMessage({ id: item.labelKey }),
  }));
  const templateOptions: SelectOption<TemplateFilter>[] = templateOptionKeys.map((item) => ({
    value: item.value,
    label: intl.formatMessage({ id: item.labelKey }),
  }));

  const handleStatusChange = (value: StatusFilter): void => {
    setStatus(value);
    setPage(1);
  };

  const handleTemplateChange = (value: TemplateFilter): void => {
    setTemplate(value);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold text-blue-600 dark:text-blue-300">T-E-12</p>
            <h2 className="mt-1 text-2xl font-black text-slate-950 dark:text-white">{intl.formatMessage({ id: 'admin.posters.title' })}</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
              {intl.formatMessage({ id: 'admin.posters.description' })}
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:min-w-[28rem]">
            <Select label={intl.formatMessage({ id: 'admin.posters.filters.status' })} value={status} options={statusOptions} onChange={handleStatusChange} />
            <Select label={intl.formatMessage({ id: 'admin.posters.filters.template' })} value={template} options={templateOptions} onChange={handleTemplateChange} />
          </div>
        </div>
      </section>

      {postersQuery.isLoading && (
        <div role="status" className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
          {intl.formatMessage({ id: 'admin.posters.loading' })}
        </div>
      )}

      {postersQuery.isError && (
        <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
          {intl.formatMessage({ id: 'admin.posters.error' })}
        </div>
      )}

      {!postersQuery.isLoading && !postersQuery.isError && (
        <>
          <section aria-label={intl.formatMessage({ id: 'admin.posters.gridAriaLabel' })} className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {posters.map((item) => (
              <article key={item.jobId} className="flex min-h-80 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <div className="flex aspect-[4/3] items-center justify-center bg-slate-100 dark:bg-slate-800">
                  {item.posterUrl ? (
                    <img src={item.posterUrl} alt={intl.formatMessage({ id: 'admin.posters.thumbnailAlt' }, { jobId: item.jobId })} className="h-full w-full object-cover" />
                  ) : (
                    <span className="text-sm text-slate-400 dark:text-slate-500">{intl.formatMessage({ id: 'admin.posters.noThumbnail' })}</span>
                  )}
                </div>
                <div className="flex flex-1 flex-col p-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${statusClass[item.status]}`}>
                      {intl.formatMessage({ id: statusLabel[item.status] })}
                    </span>
                    <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
                      {intl.formatMessage({ id: templateKey(item.template) })}
                    </span>
                  </div>
                  <h3 className="mt-4 text-lg font-bold text-slate-950 dark:text-white">{item.jobId}</h3>
                  <dl className="mt-4 space-y-2 text-sm">
                    <div className="flex justify-between gap-3">
                      <dt className="text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.posters.planId' })}</dt>
                      <dd className="font-medium text-slate-950 dark:text-white">{item.planId || '-'}</dd>
                    </div>
                    <div className="flex justify-between gap-3">
                      <dt className="text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.posters.progress' })}</dt>
                      <dd className="font-medium text-slate-950 dark:text-white">{item.progress}%</dd>
                    </div>
                    <div className="flex justify-between gap-3">
                      <dt className="text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.posters.updatedAt' })}</dt>
                      <dd className="font-medium text-slate-950 dark:text-white">{formatDate(item.updatedAt, intl.locale)}</dd>
                    </div>
                  </dl>
                  {item.posterUrl && (
                    <a href={item.posterUrl} className="mt-auto inline-flex min-h-10 items-center text-sm font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-300">
                      {intl.formatMessage({ id: 'admin.posters.openPoster' })}
                    </a>
                  )}
                </div>
              </article>
            ))}
            {posters.length === 0 && (
              <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400 md:col-span-2 xl:col-span-3">
                {intl.formatMessage({ id: 'admin.posters.empty' })}
              </div>
            )}
          </section>
          <Pagination page={page} pageSize={PAGE_SIZE} totalItems={total} onPageChange={setPage} label={intl.formatMessage({ id: 'admin.posters.pagination' })} />
        </>
      )}
    </div>
  );
}
