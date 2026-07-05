import { useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import type { PlanCardMessageData } from '@/types/message';

type TabKey = 'rush' | 'stable' | 'safe';

interface Props {
  data: PlanCardMessageData;
  userScore?: number;
  onSave?: () => void;
  onExport?: () => void;
  savedPlanId?: string;
  adjusted?: boolean;
}

const TABS: ReadonlyArray<{ key: TabKey; labelKey: string; mobileLabelKey: string; color: string; bg: string; border: string }> = [
  { key: 'rush', labelKey: 'planCard.tabs.rush', mobileLabelKey: 'planCard.tabs.rushShort', color: 'text-orange-600 dark:text-orange-300', bg: 'bg-orange-50 dark:bg-orange-500/10', border: 'border-orange-200 dark:border-orange-500/40' },
  { key: 'stable', labelKey: 'planCard.tabs.stable', mobileLabelKey: 'planCard.tabs.stableShort', color: 'text-blue-600 dark:text-blue-300', bg: 'bg-blue-50 dark:bg-blue-500/10', border: 'border-blue-200 dark:border-blue-500/40' },
  { key: 'safe', labelKey: 'planCard.tabs.safe', mobileLabelKey: 'planCard.tabs.safeShort', color: 'text-green-600 dark:text-green-300', bg: 'bg-green-50 dark:bg-green-500/10', border: 'border-green-200 dark:border-green-500/40' },
];

export function PlanCard({ data, userScore, onSave, onExport, savedPlanId, adjusted }: Props) {
  const intl = useIntl();
  const [activeTab, setActiveTab] = useState<TabKey>('rush');
  const activeConfig = TABS.find((t) => t.key === activeTab);
  const items = data[activeTab];

  return (
    <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-800">
        <div>
          <h3 className="text-sm font-bold text-gray-800 dark:text-gray-100">
            <FormattedMessage id={adjusted ? 'planCard.title.adjusted' : 'planCard.title.default'} />
          </h3>
          {userScore !== undefined && (
            <p className="text-xs text-gray-500 mt-0.5 dark:text-gray-400">
              <FormattedMessage id="planCard.basedOnScore" values={{ score: userScore }} />
            </p>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          {savedPlanId ? (
            <span className="text-xs text-green-600 dark:text-green-300">
              <FormattedMessage id="planCard.saved" />
            </span>
          ) : onSave ? (
            <button
              onClick={onSave}
              className="px-3 py-1.5 text-xs bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors dark:bg-blue-500/10 dark:text-blue-200 dark:hover:bg-blue-500/20"
              type="button"
            >
              <FormattedMessage id="planCard.save" />
            </button>
          ) : null}
          {onExport && (
            <button
              onClick={onExport}
              className="px-3 py-1.5 text-xs bg-purple-50 text-purple-600 rounded-lg hover:bg-purple-100 transition-colors dark:bg-purple-500/10 dark:text-purple-200 dark:hover:bg-purple-500/20"
              type="button"
            >
              <FormattedMessage id="planCard.export" />
            </button>
          )}
        </div>
      </div>

      <div className="flex border-b border-gray-100 dark:border-gray-800" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            role="tab"
            aria-selected={activeTab === tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 px-3 py-2.5 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? `${tab.color} ${tab.bg} border-b-2 ${tab.border} dark:border-b-current`
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100'
            }`}
          >
            <span className="hidden sm:inline">
              <FormattedMessage id={tab.labelKey} />
            </span>
            <span className="sm:hidden">
              <FormattedMessage id={tab.mobileLabelKey} />
            </span>
            <span className="ml-1 text-xs">({data[tab.key].length})</span>
          </button>
        ))}
      </div>

      <div className="divide-y divide-gray-100 dark:divide-gray-800">
        {items.length === 0 ? (
          <div className="px-4 py-8 text-center text-xs text-gray-500 dark:text-gray-400">
            <FormattedMessage id="planCard.emptyGroup" />
          </div>
        ) : (
          items.map((item, idx) => (
            <div key={`${item.university}-${idx}`} className="px-4 py-3 hover:bg-gray-50 transition-colors dark:hover:bg-gray-800/60">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-gray-800 truncate dark:text-gray-100">{item.university}</span>
                    <span className="text-xs text-gray-500 dark:text-gray-500">·</span>
                    <span className="text-xs text-gray-600 truncate dark:text-gray-300">{item.major}</span>
                  </div>
                  <p className="mt-1 text-xs text-gray-500 leading-relaxed line-clamp-2 dark:text-gray-400">{item.reason}</p>
                </div>
                <div className="flex flex-col items-end gap-0.5 flex-shrink-0">
                  <span className={`text-xs font-bold ${activeConfig?.color}`}>{item.probability}%</span>
                  <span className="text-xs text-gray-400 dark:text-gray-500">
                    {intl.formatMessage({ id: 'planCard.estimatedScore' }, { score: item.estScore })}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
