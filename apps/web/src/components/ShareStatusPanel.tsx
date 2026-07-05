/**
 * Sprint 6 T-D-15 · ShareStatusPanel
 *
 * Composite panel for latest share link state, stats and access trend.
 */
import { BarChart3 } from 'lucide-react';
import { FormattedMessage, useIntl } from 'react-intl';
import { AccessTrendChart, type AccessDataPoint } from './AccessTrendChart';
import { StatsCard } from './StatsCard';
import type { ShareLinkResponse } from '@/hooks/useShareLink';

interface ShareStatusPanelProps {
  latest: ShareLinkResponse | null | undefined;
  isLoading?: boolean;
  isError?: boolean;
  trend: ReadonlyArray<AccessDataPoint>;
  onCreate: () => void;
  onRetry?: () => void;
}

export function ShareStatusPanel({ latest, isLoading = false, isError = false, trend, onCreate, onRetry }: ShareStatusPanelProps) {
  const intl = useIntl();

  if (isLoading) {
    return (
      <div className="rounded-xl border border-gray-100 bg-white p-8 text-center shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <BarChart3 className="w-12 h-12 mx-auto text-blue-300 dark:text-blue-500" aria-hidden="true" />
        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400" role="status">
          <FormattedMessage id="share.status.loading" />
        </p>
      </div>
    );
  }

  if (!latest) {
    return (
      <div className="rounded-xl border border-dashed border-gray-200 bg-gray-50 p-8 text-center dark:border-gray-700 dark:bg-gray-900">
        <BarChart3 className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600" aria-hidden="true" />
        {isError ? (
          <p className="mt-2 text-sm text-amber-700 dark:text-amber-300" role="alert">
            <FormattedMessage id="share.status.unavailable" />
          </p>
        ) : (
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            <FormattedMessage id="share.status.empty" />
          </p>
        )}
        {isError && onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-4 inline-flex min-h-[48px] px-5 py-2.5 rounded-xl border border-amber-200 bg-amber-50 text-sm font-medium text-amber-800 hover:bg-amber-100 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200"
          >
            <FormattedMessage id="share.status.retry" />
          </button>
        )}
        <button
          type="button"
          onClick={onCreate}
          className="mt-4 inline-flex min-h-[48px] px-5 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
        >
          <FormattedMessage id="share.status.createFirst" />
        </button>
      </div>
    );
  }

  return (
    <section className="grid gap-4" role="region" aria-label={intl.formatMessage({ id: 'share.status.ariaLabel' })}>
      <StatsCard code={latest.code} />
      <AccessTrendChart data={trend} />
      <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <p className="text-xs font-semibold text-gray-400 mb-2 dark:text-gray-500">
          <FormattedMessage id="share.status.latestLink" />
        </p>
        <div className="mb-3 inline-flex items-center rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700 dark:bg-blue-950/50 dark:text-blue-300">
          {latest.code}
        </div>
        <p className="text-sm text-gray-800 break-all dark:text-gray-100">{latest.url}</p>
        <p className="mt-2 text-xs text-gray-400 dark:text-gray-500">
          <FormattedMessage
            id="share.status.createdAt"
            values={{ date: intl.formatDate(new Date(latest.createdAt), { dateStyle: 'medium', timeStyle: 'medium' }) }}
          />
        </p>
      </div>
    </section>
  );
}
