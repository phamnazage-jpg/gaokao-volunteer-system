import { Link } from 'react-router-dom';
import { FormattedMessage } from 'react-intl';
import { usePlansQuery } from '@/hooks/usePlanQueries';

export function PlanComparePage() {
  const { data, isLoading, error } = usePlansQuery();
  const plans = data?.plans ?? [];

  return (
    <main className="flex-1 overflow-y-auto px-4 py-6 pb-20 lg:pb-6">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">
            <FormattedMessage id="planCompare.title" />
          </h1>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            <FormattedMessage id="planCompare.description" />
          </p>
        </div>
        <Link to="/plans" className="rounded-xl border border-gray-200 px-3 py-2 text-xs text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800">
          <FormattedMessage id="plans.title" />
        </Link>
      </div>

      {isLoading && (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          <FormattedMessage id="common.loading" />
        </p>
      )}
      {error && (
        <p className="rounded-xl border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300" role="alert">
          <FormattedMessage id="planCompare.error" />
        </p>
      )}

      {!isLoading && !error && plans.length === 0 && (
        <section className="rounded-3xl border border-dashed border-gray-300 bg-white p-8 text-center dark:border-gray-700 dark:bg-gray-900">
          <div className="text-4xl" aria-hidden="true">📋</div>
          <h2 className="mt-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
            <FormattedMessage id="planCompare.empty.title" />
          </h2>
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            <FormattedMessage id="planCompare.empty.description" />
          </p>
          <Link to="/" className="mt-5 inline-flex rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
            <FormattedMessage id="plans.empty.action" />
          </Link>
        </section>
      )}

      {plans.length > 0 && (
        <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 dark:bg-gray-800 dark:text-gray-300">
              <tr>
                <th className="px-4 py-3 font-medium">
                  <FormattedMessage id="planCompare.columns.plan" />
                </th>
                <th className="px-4 py-3 font-medium">
                  <FormattedMessage id="planGroups.rush" />
                </th>
                <th className="px-4 py-3 font-medium">
                  <FormattedMessage id="planGroups.stable" />
                </th>
                <th className="px-4 py-3 font-medium">
                  <FormattedMessage id="planGroups.safe" />
                </th>
              </tr>
            </thead>
            <tbody>
              {plans.map((plan) => (
                <tr key={plan.id} className="border-t border-gray-100 dark:border-gray-800">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{plan.name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{plan.rush.length}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{plan.stable.length}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{plan.safe.length}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
