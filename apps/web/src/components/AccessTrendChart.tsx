import { useIntl } from 'react-intl';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';

export interface AccessDataPoint {
  readonly date: string;
  readonly views: number;
}

interface Props {
  data: ReadonlyArray<AccessDataPoint>;
}

export function AccessTrendChart({ data }: Props) {
  const intl = useIntl();
  const title = intl.formatMessage({ id: 'share.trend.title' });

  return (
    <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900" role="img" aria-label={title}>
      <p className="text-xs font-semibold text-gray-400 mb-2 dark:text-gray-500">{title}</p>
      <div className="h-32">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={[...data]}>
            <XAxis dataKey="date" stroke="#9CA3AF" fontSize={10} />
            <YAxis stroke="#9CA3AF" fontSize={10} width={24} />
            <Tooltip
              contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E5E7EB' }}
            />
            <Line type="monotone" dataKey="views" stroke="#3B82F6" strokeWidth={2} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
