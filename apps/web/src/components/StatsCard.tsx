import { FormattedMessage, useIntl } from 'react-intl';
import { Eye, Users, Clock } from 'lucide-react';
import { useShareLinkStatsQuery } from '@/hooks/useShareLink';

interface Props {
  code: string;
}

interface Card {
  readonly labelId: string;
  readonly value: string | number;
  readonly icon: React.ReactNode;
}

export function StatsCard({ code }: Props) {
  const intl = useIntl();
  const { data, isError, isLoading } = useShareLinkStatsQuery(code);

  const cards: ReadonlyArray<Card> = [
    {
      labelId: 'share.stats.views',
      value: isLoading ? '—' : (data?.views ?? 0),
      icon: <Eye className="w-4 h-4" />,
    },
    {
      labelId: 'share.stats.uniqueVisitors',
      value: isLoading ? '—' : (data?.uniqueVisitors ?? 0),
      icon: <Users className="w-4 h-4" />,
    },
    {
      labelId: 'share.stats.lastAccessed',
      value: data?.lastAccessedAt
        ? intl.formatDate(new Date(data.lastAccessedAt), { dateStyle: 'short', timeStyle: 'medium' })
        : '—',
      icon: <Clock className="w-4 h-4" />,
    },
  ];

  if (isError) {
    return (
      <div className="rounded-lg border border-amber-100 bg-amber-50 px-3 py-2 text-sm text-amber-700 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-300" role="status">
        <FormattedMessage id="share.stats.unavailable" />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-3 gap-3" role="list" aria-label={intl.formatMessage({ id: 'share.stats.ariaLabel' })}>
      {cards.map((card) => (
        <div
          key={card.labelId}
          role="listitem"
          className="rounded-xl border border-gray-100 bg-white p-3 shadow-sm dark:border-gray-800 dark:bg-gray-900"
        >
          <div className="flex items-center gap-1.5 text-xs text-gray-400 dark:text-gray-500">
            {card.icon}
            <span>
              <FormattedMessage id={card.labelId} />
            </span>
          </div>
          <p className="mt-1.5 text-lg font-semibold text-gray-800 truncate dark:text-gray-100">{card.value}</p>
        </div>
      ))}
    </div>
  );
}
