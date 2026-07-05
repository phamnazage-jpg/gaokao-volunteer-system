import { useParams } from 'react-router-dom';
import { FormattedMessage, useIntl } from 'react-intl';
import { usePlanQuery } from '@/hooks/usePlanQueries';

export function PlanDetailPage() {
  const intl = useIntl();
  const { planId } = useParams<{ planId: string }>();
  const { data, isLoading, error } = usePlanQuery(planId ?? null);

  if (isLoading) {
    return (
      <div className="p-4 text-sm text-gray-500 dark:text-gray-400">
        <FormattedMessage id="common.loading" />
      </div>
    );
  }
  if (error) {
    return (
      <div className="m-4 rounded-xl border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300" role="alert">
        <FormattedMessage id="planDetail.error" />
      </div>
    );
  }
  if (!data) {
    return (
      <div className="p-4 text-sm text-gray-500 dark:text-gray-400">
        <FormattedMessage id="planDetail.notFound" />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 dark:text-gray-100">
      <h1 className="text-lg font-bold mb-4">{data.name}</h1>
      <div className="space-y-4">
        <section>
          <h2 className="text-sm font-semibold mb-2">
            <FormattedMessage id="planDetail.groupTitle" values={{ icon: '🚀', label: intl.formatMessage({ id: 'planGroups.rush' }), count: data.rush.length }} />
          </h2>
        </section>
        <section>
          <h2 className="text-sm font-semibold mb-2">
            <FormattedMessage id="planDetail.groupTitle" values={{ icon: '🎯', label: intl.formatMessage({ id: 'planGroups.stable' }), count: data.stable.length }} />
          </h2>
        </section>
        <section>
          <h2 className="text-sm font-semibold mb-2">
            <FormattedMessage id="planDetail.groupTitle" values={{ icon: '🛡️', label: intl.formatMessage({ id: 'planGroups.safe' }), count: data.safe.length }} />
          </h2>
        </section>
      </div>
    </div>
  );
}
