/**
 * V10 · Sprint 3 · AccessTrendChart
 *
 * 访问趋势 mini chart (recharts)
 * V10 收益：Sprint 5 chart 任务的预演
 */
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';

export interface AccessDataPoint {
  readonly date: string;
  readonly views: number;
}

interface Props {
  data: ReadonlyArray<AccessDataPoint>;
}

export function AccessTrendChart({ data }: Props) {
  return (
    <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm" role="img" aria-label="访问趋势">
      <p className="text-xs font-semibold text-gray-400 mb-2">访问趋势</p>
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