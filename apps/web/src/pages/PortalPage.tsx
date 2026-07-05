import { useParams } from 'react-router-dom';
import { ExternalLink, TrendingUp } from 'lucide-react';
import { FormattedMessage, useIntl } from 'react-intl';
import { usePortalCWBQuery, usePortalFullPlanQuery } from '@/hooks/usePortal';

const RUSH_PROBABILITY = '\u51b2';
const STABLE_PROBABILITY = '\u7a33';

function getAdmissionProbabilityMeta(probability: string): { className: string; labelKey: string } {
  if (probability === RUSH_PROBABILITY) {
    return { className: 'bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-200', labelKey: 'portal.probability.rush' };
  }
  if (probability === STABLE_PROBABILITY) {
    return { className: 'bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-200', labelKey: 'portal.probability.stable' };
  }
  return { className: 'bg-green-50 text-green-600 dark:bg-green-950/40 dark:text-green-200', labelKey: 'portal.probability.safe' };
}

export function PortalPage() {
  const intl = useIntl();
  const { token = '' } = useParams<{ token: string }>();
  const cwb = usePortalCWBQuery(token);
  const fullPlan = usePortalFullPlanQuery(token);
  const hasError = cwb.isError || fullPlan.isError;
  const hasData = Boolean(cwb.data || fullPlan.data);

  if (cwb.isLoading || fullPlan.isLoading) {
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <p className="text-sm text-gray-500 dark:text-gray-400">
          <FormattedMessage id="portal.loading" />
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">
        <FormattedMessage id="portal.title" />
      </h1>
      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
        <FormattedMessage id="portal.description" />
      </p>

      {hasError && (
        <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200" role="alert">
          <FormattedMessage id="portal.error" />
        </div>
      )}

      {!hasError && !hasData && (
        <div className="mt-6 rounded-xl border border-gray-100 bg-white p-6 text-sm text-gray-600 shadow-sm dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300">
          <FormattedMessage id="portal.empty" />
        </div>
      )}

      {cwb.data && (
        <div className="mt-6 rounded-xl border border-gray-100 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <p className="text-xs text-gray-400 dark:text-gray-500">
            <FormattedMessage id="portal.cwb.title" />
          </p>
          <div className="mt-2 grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs text-gray-400 dark:text-gray-500">
                <FormattedMessage id="portal.cwb.province" />
              </p>
              <p className="text-sm font-semibold text-gray-800 dark:text-gray-100">{cwb.data.province}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 dark:text-gray-500">
                <FormattedMessage id="portal.cwb.year" />
              </p>
              <p className="text-sm font-semibold text-gray-800 dark:text-gray-100">{cwb.data.year}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 dark:text-gray-500">
                <FormattedMessage id="portal.cwb.score" />
              </p>
              <p className="text-sm font-semibold text-gray-800 dark:text-gray-100">{cwb.data.score}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 dark:text-gray-500">
                <FormattedMessage id="portal.cwb.rank" />
              </p>
              <p className="text-sm font-semibold text-gray-800 dark:text-gray-100">{cwb.data.rank.toLocaleString()}</p>
            </div>
          </div>
          <div className="mt-3 flex items-center gap-2 text-blue-600 text-sm dark:text-blue-300">
            <TrendingUp className="w-4 h-4" />
            <span>
              <FormattedMessage id="portal.cwb.equivalentScore" values={{ score: cwb.data.equivalentScore }} />
            </span>
          </div>
        </div>
      )}

      {fullPlan.data && (
        <div className="mt-6 rounded-xl border border-gray-100 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <p className="text-xs font-semibold text-gray-400 mb-3 dark:text-gray-500">{fullPlan.data.plan.title}</p>
          <ul className="space-y-3">
            {fullPlan.data.plan.schools.map((school) => {
              const probabilityMeta = getAdmissionProbabilityMeta(school.admissionProbability);
              return (
                <li key={school.id} className="border-b border-gray-100 pb-3 last:border-0 last:pb-0 dark:border-gray-800">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-gray-800 dark:text-gray-100">{school.name}</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${probabilityMeta.className}`}>
                      <FormattedMessage id={probabilityMeta.labelKey} />
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    <FormattedMessage
                      id="portal.plan.majors"
                      values={{ majors: school.majors.join(intl.formatMessage({ id: 'portal.plan.majorsSeparator' })) }}
                    />
                  </p>
                </li>
              );
            })}
          </ul>
          <a
            href="/portal/full"
            className="mt-4 inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-300 dark:hover:text-blue-200"
          >
            <FormattedMessage id="portal.plan.openFull" /> <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      )}
    </div>
  );
}
