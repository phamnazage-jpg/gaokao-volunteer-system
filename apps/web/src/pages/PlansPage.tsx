import { useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { usePlansQuery } from '@/hooks/usePlanQueries';
import { CardListSkeleton } from '@/components/shared/Skeleton';
import { EmptyState } from '@/components/shared/EmptyState';
import { Pagination } from '@/components/shared/Pagination';

const PAGE_SIZE = 5;

export function PlansPage() {
  const intl = useIntl();
  const { data, isLoading, error } = usePlansQuery();
  const [page, setPage] = useState(1);
  const plans = data?.plans ?? [];
  const visiblePlans = plans.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <h1 className="text-lg font-bold mb-4 dark:text-gray-100">
        <FormattedMessage id="plans.title" />
      </h1>

      {isLoading && <CardListSkeleton label={intl.formatMessage({ id: 'plans.loading' })} />}
      {error && (
        <p className="rounded-xl border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300" role="alert">
          <FormattedMessage id="plans.error" />
        </p>
      )}

      <div className="space-y-3" aria-label={intl.formatMessage({ id: 'plans.listAriaLabel' })}>
        {visiblePlans.map((plan) => (
          <a key={plan.id} href={`/plans/${plan.id}`} className="block bg-white border border-gray-200 rounded-2xl p-4 hover:shadow-md transition-shadow dark:border-gray-800 dark:bg-gray-900">
            <h2 className="text-sm font-medium text-gray-800 dark:text-gray-100">{plan.name}</h2>
            <p className="text-xs text-gray-500 mt-1 dark:text-gray-400">
              <FormattedMessage
                id="plans.createdAt"
                values={{
                  date: intl.formatDate(new Date(plan.createdAt), {
                    dateStyle: 'medium',
                    timeStyle: 'short',
                  }),
                }}
              />
            </p>
          </a>
        ))}

        {data?.plans.length === 0 && (
          <EmptyState
            title={intl.formatMessage({ id: 'plans.empty.title' })}
            description={intl.formatMessage({ id: 'plans.empty.description' })}
            actionLabel={intl.formatMessage({ id: 'plans.empty.action' })}
            actionHref="/"
          />
        )}
      </div>
      <Pagination page={page} pageSize={PAGE_SIZE} totalItems={plans.length} onPageChange={setPage} label={intl.formatMessage({ id: 'plans.pagination' })} />
    </div>
  );
}
