import { useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { SafeMarkdown } from './shared/SafeMarkdown';
import type { CareerCardMessageData } from '@/types/message';

interface Props {
  data: CareerCardMessageData;
}

type CareerProspect = CareerCardMessageData['careers'][number]['prospect'];

const PROSPECT_STYLES = {
  '\u597d': { color: 'text-green-700', bg: 'bg-green-50', labelKey: 'careerCard.prospect.good' },
  '\u4e2d': { color: 'text-yellow-700', bg: 'bg-yellow-50', labelKey: 'careerCard.prospect.medium' },
  '\u5dee': { color: 'text-red-700', bg: 'bg-red-50', labelKey: 'careerCard.prospect.poor' },
} satisfies Record<CareerProspect, { color: string; bg: string; labelKey: string }>;

export function CareerCard({ data }: Props) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? data.careers : data.careers.slice(0, 3);

  return (
    <div className="mt-2 bg-white border border-gray-200 rounded-2xl rounded-tl-md shadow-sm overflow-hidden dark:border-gray-800 dark:bg-gray-900">
      <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800">
        <h3 className="text-sm font-bold text-gray-800 dark:text-gray-100">
          <FormattedMessage id="careerCard.title" />
        </h3>
        <p className="text-xs text-gray-500 mt-0.5 dark:text-gray-400">
          <FormattedMessage id="careerCard.description" />
        </p>
      </div>

      <div className="divide-y divide-gray-100 dark:divide-gray-800">
        {visible.map((career, idx) => {
          const style = PROSPECT_STYLES[career.prospect];
          return (
            <div key={`${career.name}-${idx}`} className="px-4 py-3 hover:bg-gray-50 transition-colors dark:hover:bg-gray-800/60">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-gray-800 dark:text-gray-100">{career.name}</h4>
                  <SafeMarkdown content={career.description} />
                </div>
                <div className="flex flex-col items-end gap-0.5 flex-shrink-0">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${style.bg} ${style.color}`}>
                    <FormattedMessage id={style.labelKey} />
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">{career.salary}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {data.careers.length > 3 && (
        <div className="px-4 py-2 text-center border-t border-gray-100 dark:border-gray-800">
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-300 dark:hover:text-blue-200"
          >
            <FormattedMessage id={expanded ? 'careerCard.collapse' : 'careerCard.expandRemaining'} values={{ count: data.careers.length - 3 }} />
          </button>
        </div>
      )}
    </div>
  );
}
