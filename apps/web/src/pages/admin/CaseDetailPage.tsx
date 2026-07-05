import { Link, useParams } from 'react-router-dom';
import { useIntl } from 'react-intl';
import { SafeMarkdown } from '@/components/shared/SafeMarkdown';
import { useAdminCaseQuery } from '@/hooks/useAdminCases';

const categoryLabel: Record<string, string> = {
  success: 'admin.cases.category.success',
  typical: 'admin.cases.category.typical',
  warning: 'admin.cases.category.warning',
};

const reviewLabel: Record<string, string> = {
  pending: 'admin.cases.review.pending',
  approved: 'admin.cases.review.approved',
  rejected: 'admin.cases.review.rejected',
};

function parseCaseId(value: string | undefined): number | null {
  if (!value) return null;
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
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

export function AdminCaseDetailPage() {
  const intl = useIntl();
  const { caseId } = useParams();
  const numericCaseId = parseCaseId(caseId);
  const caseQuery = useAdminCaseQuery(numericCaseId);
  const detail = caseQuery.data;
  const formatCategory = (category: string): string => (categoryLabel[category] ? intl.formatMessage({ id: categoryLabel[category] }) : category);
  const formatReview = (reviewStatus: string): string => (reviewLabel[reviewStatus] ? intl.formatMessage({ id: reviewLabel[reviewStatus] }) : reviewStatus);

  if (!numericCaseId) {
    return (
      <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
        {intl.formatMessage({ id: 'admin.caseDetail.invalidId' })}
      </div>
    );
  }

  if (caseQuery.isLoading) {
    return (
      <div role="status" className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
        {intl.formatMessage({ id: 'admin.caseDetail.loading' })}
      </div>
    );
  }

  if (caseQuery.isError || !detail) {
    return (
      <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
        {intl.formatMessage({ id: 'admin.caseDetail.error' })}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <Link to="/admin/cases" className="text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-300">
          {intl.formatMessage({ id: 'admin.caseDetail.backToCases' })}
        </Link>
        <p className="mt-4 text-sm font-semibold text-blue-600 dark:text-blue-300">T-E-09</p>
        <h2 className="mt-1 text-3xl font-black leading-tight text-slate-950 dark:text-white">{detail.title}</h2>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-500 dark:text-slate-400">{detail.summary ?? intl.formatMessage({ id: 'admin.cases.noSummary' })}</p>
        <div className="mt-5 flex flex-wrap gap-2 text-xs font-semibold">
          <span className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-blue-700 dark:border-blue-500/30 dark:bg-blue-500/10 dark:text-blue-200">
            {formatCategory(detail.category)}
          </span>
          <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
            {formatReview(detail.reviewStatus)}
          </span>
          {detail.tags.map((tag) => (
            <span key={tag} className="rounded-full bg-slate-100 px-3 py-1 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
              {tag}
            </span>
          ))}
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <p className="text-xs text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.caseDetail.reviewer' })}</p>
          <p className="mt-2 text-lg font-bold text-slate-950 dark:text-white">{detail.reviewer ?? intl.formatMessage({ id: 'admin.orders.fallback.unassigned' })}</p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <p className="text-xs text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.caseDetail.reviewedAt' })}</p>
          <p className="mt-2 text-lg font-bold text-slate-950 dark:text-white">{formatDate(detail.reviewedAt, intl.locale)}</p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <p className="text-xs text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.caseDetail.updatedAt' })}</p>
          <p className="mt-2 text-lg font-bold text-slate-950 dark:text-white">{formatDate(detail.updatedAt, intl.locale)}</p>
        </article>
      </section>

      {detail.reviewNote && (
        <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm leading-6 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100">
          <h3 className="font-bold">{intl.formatMessage({ id: 'admin.caseDetail.reviewNote' })}</h3>
          <p className="mt-2">{detail.reviewNote}</p>
        </section>
      )}

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h3 className="text-base font-bold text-slate-950 dark:text-white">{intl.formatMessage({ id: 'admin.caseDetail.body' })}</h3>
        <div className="mt-4 text-sm leading-7 text-slate-700 dark:text-slate-300">
          <SafeMarkdown content={detail.content ?? intl.formatMessage({ id: 'admin.caseDetail.noBody' })} />
        </div>
      </section>
    </div>
  );
}
