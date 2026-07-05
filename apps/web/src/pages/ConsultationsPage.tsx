import { useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { useConsultationsQuery } from '@/hooks/useConsultationQueries';
import { CardListSkeleton } from '@/components/shared/Skeleton';
import { EmptyState } from '@/components/shared/EmptyState';
import { Pagination } from '@/components/shared/Pagination';
import { Avatar } from '@/components/shared/Avatar';
import { DatePicker } from '@/components/shared/DatePicker';

const PAGE_SIZE = 5;

export function ConsultationsPage() {
  const intl = useIntl();
  const { data, isLoading, error } = useConsultationsQuery();
  const [page, setPage] = useState(1);
  const [updatedAfter, setUpdatedAfter] = useState('');
  const consultations = data?.consultations ?? [];
  const filteredConsultations = updatedAfter
    ? consultations.filter((consultation) => consultation.updatedAt.slice(0, 10) >= updatedAfter)
    : consultations;
  const visibleConsultations = filteredConsultations.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const handleUpdatedAfterChange = (value: string): void => {
    setUpdatedAfter(value);
    setPage(1);
  };

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <h1 className="text-lg font-bold dark:text-gray-100">
          <FormattedMessage id="consultations.title" />
        </h1>
        <DatePicker
          label={intl.formatMessage({ id: 'consultations.updatedAfterLabel' })}
          value={updatedAfter}
          onChange={handleUpdatedAfterChange}
          helpText={intl.formatMessage({ id: 'consultations.updatedAfterHelp' })}
          className="sm:w-56"
        />
      </div>
      {isLoading && <CardListSkeleton label={intl.formatMessage({ id: 'consultations.loading' })} />}
      {error && (
        <p className="rounded-xl border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300" role="alert">
          <FormattedMessage id="consultations.error" />
        </p>
      )}
      <div className="space-y-3" aria-label={intl.formatMessage({ id: 'consultations.listAriaLabel' })}>
        {visibleConsultations.map((c) => (
          <div key={c.id} className="flex items-center gap-3 bg-white border border-gray-200 rounded-2xl p-4 dark:border-gray-800 dark:bg-gray-900">
            <Avatar name={c.title} />
            <div className="min-w-0">
              <h2 className="truncate text-sm font-medium text-gray-800 dark:text-gray-100">{c.title}</h2>
              <p className="text-xs text-gray-500 mt-1 dark:text-gray-400">
                <FormattedMessage
                  id="consultations.meta"
                  values={{
                    count: c.messageCount,
                    date: intl.formatDate(new Date(c.updatedAt), {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    }),
                  }}
                />
              </p>
            </div>
          </div>
        ))}
        {consultations.length === 0 && (
          <EmptyState
            title={intl.formatMessage({ id: 'consultations.empty.title' })}
            description={intl.formatMessage({ id: 'consultations.empty.description' })}
            actionLabel={intl.formatMessage({ id: 'consultations.empty.action' })}
            actionHref="/"
          />
        )}
        {consultations.length > 0 && filteredConsultations.length === 0 && (
          <EmptyState
            title={intl.formatMessage({ id: 'consultations.noFiltered.title' })}
            description={intl.formatMessage({ id: 'consultations.noFiltered.description' })}
          />
        )}
      </div>
      <Pagination page={page} pageSize={PAGE_SIZE} totalItems={filteredConsultations.length} onPageChange={setPage} label={intl.formatMessage({ id: 'consultations.pagination' })} />
    </div>
  );
}
