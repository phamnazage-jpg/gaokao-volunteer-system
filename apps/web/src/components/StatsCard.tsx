/**
 * V10 · Sprint 3 · StatsCard
 *
 * 3 卡片：访问数 / 独立访客 / 最近访问
 */
import { Eye, Users, Clock } from 'lucide-react';
import { useShareLinkStatsQuery } from '@/hooks/useShareLink';

interface Props {
  code: string;
}

interface Card {
  readonly label: string;
  readonly value: string | number;
  readonly icon: React.ReactNode;
}

export function StatsCard({ code }: Props) {
  const { data, isLoading } = useShareLinkStatsQuery(code);

  const cards: ReadonlyArray<Card> = [
    {
      label: '访问数',
      value: isLoading ? '—' : (data?.views ?? 0),
      icon: <Eye className="w-4 h-4" />,
    },
    {
      label: '独立访客',
      value: isLoading ? '—' : (data?.uniqueVisitors ?? 0),
      icon: <Users className="w-4 h-4" />,
    },
    {
      label: '最近访问',
      value: data?.lastAccessedAt ? new Date(data.lastAccessedAt).toLocaleString('zh-CN', { hour12: false }) : '—',
      icon: <Clock className="w-4 h-4" />,
    },
  ];

  return (
    <div className="grid grid-cols-3 gap-3" role="list" aria-label="分享统计">
      {cards.map((card) => (
        <div
          key={card.label}
          role="listitem"
          className="rounded-xl border border-gray-100 bg-white p-3 shadow-sm"
        >
          <div className="flex items-center gap-1.5 text-xs text-gray-400">
            {card.icon}
            <span>{card.label}</span>
          </div>
          <p className="mt-1.5 text-lg font-semibold text-gray-800 truncate">{card.value}</p>
        </div>
      ))}
    </div>
  );
}