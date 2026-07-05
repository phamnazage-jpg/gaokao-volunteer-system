import { FormattedMessage, useIntl } from 'react-intl';
import type { AuditReportMessageData } from '@/types/message';

interface Props {
  data: AuditReportMessageData;
  onFixRequest?: (riskIndex: number, riskText: string) => void;
  savedPlanId?: string;
}

type RiskLevel = AuditReportMessageData['risks'][number]['level'];

const LEVEL_STYLES = {
  '\u4f4e': { color: 'text-green-700', bg: 'bg-green-50', labelKey: 'auditReport.level.low' },
  '\u4e2d': { color: 'text-yellow-700', bg: 'bg-yellow-50', labelKey: 'auditReport.level.medium' },
  '\u9ad8': { color: 'text-red-700', bg: 'bg-red-50', labelKey: 'auditReport.level.high' },
} satisfies Record<RiskLevel, { color: string; bg: string; labelKey: string }>;

export function AuditReportCard({ data, onFixRequest, savedPlanId }: Props) {
  const intl = useIntl();
  const scoreColor = data.score >= 80 ? 'text-green-600' : data.score >= 60 ? 'text-yellow-600' : 'text-red-600';

  return (
    <div className="mt-2 bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-amber-50 to-orange-50 border-b border-amber-100 dark:border-amber-500/20 dark:from-amber-500/10 dark:to-orange-500/10">
        <div>
          <h3 className="text-sm font-bold text-amber-800 dark:text-amber-100">
            <FormattedMessage id="auditReport.title" />
          </h3>
          {savedPlanId && (
            <p className="text-xs text-amber-600 mt-0.5 dark:text-amber-300">
              <FormattedMessage id="auditReport.planId" values={{ id: savedPlanId.slice(0, 6) }} />
            </p>
          )}
        </div>
        <div className="text-right">
          <div className={`text-2xl font-bold ${scoreColor}`} aria-label={intl.formatMessage({ id: 'auditReport.scoreAriaLabel' }, { score: data.score })}>
            {data.score}
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            <FormattedMessage id="auditReport.scoreTotal" />
          </p>
        </div>
      </div>

      <div className="divide-y divide-gray-100 dark:divide-gray-800">
        {data.risks.length === 0 ? (
          <div className="px-4 py-6 text-center text-sm text-green-600 dark:text-green-300">
            <FormattedMessage id="auditReport.empty" />
          </div>
        ) : (
          data.risks.map((risk) => {
            const style = LEVEL_STYLES[risk.level];
            return (
              <div key={risk.index} className={`px-4 py-3 ${style.bg}`}>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-bold ${style.color}`}>
                        <FormattedMessage id={style.labelKey} />
                      </span>
                      <span className="text-sm font-medium text-gray-800 dark:text-gray-100">{risk.title}</span>
                    </div>
                    <p className="mt-1 text-xs text-gray-600 leading-relaxed dark:text-gray-300">{risk.description}</p>
                  </div>
                  {onFixRequest && (
                    <button
                      type="button"
                      onClick={() => onFixRequest(risk.index, risk.title)}
                      className="flex-shrink-0 px-2.5 py-1 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors dark:text-blue-300 dark:hover:bg-blue-500/10 dark:hover:text-blue-200"
                    >
                      <FormattedMessage id="auditReport.fixAction" />
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
