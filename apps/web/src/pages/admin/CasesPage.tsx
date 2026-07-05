import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useIntl } from 'react-intl';
import { Pagination } from '@/components/shared/Pagination';
import { Select, type SelectOption } from '@/components/shared/Select';
import {
  useAdminCasesQuery,
  type AdminCaseCategory,
  type AdminCaseReviewStatus,
} from '@/hooks/useAdminCases';

type CategoryFilter = AdminCaseCategory | 'all';
type ReviewFilter = AdminCaseReviewStatus | 'all';

const PAGE_SIZE = 12;

const categoryOptionKeys: Array<{ value: CategoryFilter; labelKey: string }> = [
  { value: 'all', labelKey: 'admin.cases.category.all' },
  { value: 'success', labelKey: 'admin.cases.category.success' },
  { value: 'typical', labelKey: 'admin.cases.category.typical' },
  { value: 'warning', labelKey: 'admin.cases.category.warning' },
];

const reviewOptionKeys: Array<{ value: ReviewFilter; labelKey: string }> = [
  { value: 'all', labelKey: 'admin.cases.review.all' },
  { value: 'pending', labelKey: 'admin.cases.review.pending' },
  { value: 'approved', labelKey: 'admin.cases.review.approved' },
  { value: 'rejected', labelKey: 'admin.cases.review.rejected' },
];

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

const categoryClass: Record<string, string> = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200',
  typical: 'border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-500/30 dark:bg-blue-500/10 dark:text-blue-200',
  warning: 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200',
};

export function AdminCasesPage() {
  const intl = useIntl();
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState<CategoryFilter>('all');
  const [reviewStatus, setReviewStatus] = useState<ReviewFilter>('all');

  const params = useMemo(
    () => ({
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
      category: category === 'all' ? undefined : category,
      reviewStatus: reviewStatus === 'all' ? undefined : reviewStatus,
    }),
    [category, page, reviewStatus],
  );
  const casesQuery = useAdminCasesQuery(params);
  const cases = casesQuery.data?.items ?? [];
  const total = casesQuery.data?.total ?? cases.length;
  const categoryOptions: SelectOption<CategoryFilter>[] = categoryOptionKeys.map((item) => ({
    value: item.value,
    label: intl.formatMessage({ id: item.labelKey }),
  }));
  const reviewOptions: SelectOption<ReviewFilter>[] = reviewOptionKeys.map((item) => ({
    value: item.value,
    label: intl.formatMessage({ id: item.labelKey }),
  }));

  const handleCategoryChange = (value: CategoryFilter): void => {
    setCategory(value);
    setPage(1);
  };

  const handleReviewChange = (value: ReviewFilter): void => {
    setReviewStatus(value);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold text-blue-600 dark:text-blue-300">T-E-08</p>
            <h2 className="mt-1 text-2xl font-black text-slate-950 dark:text-white">{intl.formatMessage({ id: 'admin.cases.title' })}</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
              {intl.formatMessage({ id: 'admin.cases.description' })}
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:min-w-[28rem]">
            <Select label={intl.formatMessage({ id: 'admin.cases.filters.category' })} value={category} options={categoryOptions} onChange={handleCategoryChange} />
            <Select label={intl.formatMessage({ id: 'admin.cases.filters.review' })} value={reviewStatus} options={reviewOptions} onChange={handleReviewChange} />
          </div>
        </div>
      </section>

      {casesQuery.isLoading && (
        <div role="status" className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
          {intl.formatMessage({ id: 'admin.cases.loading' })}
        </div>
      )}

      {casesQuery.isError && (
        <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
          {intl.formatMessage({ id: 'admin.cases.error' })}
        </div>
      )}

      {!casesQuery.isLoading && !casesQuery.isError && (
        <section aria-label={intl.formatMessage({ id: 'admin.cases.gridAriaLabel' })} className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {cases.map((item) => (
            <article key={item.id} className="flex min-h-64 flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="flex flex-wrap gap-2">
                <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${categoryClass[item.category] ?? categoryClass.typical}`}>
                  {categoryLabel[item.category] ? intl.formatMessage({ id: categoryLabel[item.category] }) : item.category}
                </span>
                <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
                  {reviewLabel[item.reviewStatus] ? intl.formatMessage({ id: reviewLabel[item.reviewStatus] }) : item.reviewStatus}
                </span>
              </div>
              <h3 className="mt-4 text-lg font-bold leading-7 text-slate-950 dark:text-white">{item.title}</h3>
              <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-500 dark:text-slate-400">{item.summary ?? intl.formatMessage({ id: 'admin.cases.noSummary' })}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {item.tags.map((tag) => (
                  <span key={tag} className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                    {tag}
                  </span>
                ))}
              </div>
              <Link to={`/admin/cases/${item.id}`} className="mt-auto inline-flex min-h-10 items-center text-sm font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-300">
                {intl.formatMessage({ id: 'admin.cases.viewDetail' })}
              </Link>
            </article>
          ))}
          {cases.length === 0 && (
            <div className="md:col-span-2 xl:col-span-3 rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
              {intl.formatMessage({ id: 'admin.cases.empty' })}
            </div>
          )}
        </section>
      )}

      {!casesQuery.isLoading && !casesQuery.isError && (
        <Pagination page={page} pageSize={PAGE_SIZE} totalItems={total} onPageChange={setPage} label={intl.formatMessage({ id: 'admin.cases.pagination' })} />
      )}
    </div>
  );
}
