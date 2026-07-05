import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useIntl } from 'react-intl';

export interface ChartPoint {
  label: string;
  value: number;
}

interface ChartCardProps {
  title: string;
  data: ChartPoint[];
  ariaLabel: string;
  emptyText?: string;
}

const COLORS = ['#2563EB', '#0891B2', '#16A34A', '#F59E0B', '#EF4444'];

function ChartCard({ title, data, ariaLabel, emptyText, children }: ChartCardProps & { children: React.ReactNode }) {
  const intl = useIntl();
  const resolvedEmptyText = emptyText ?? intl.formatMessage({ id: 'charts.empty' });

  return (
    <section className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900" role="img" aria-label={ariaLabel}>
      <p className="mb-2 text-xs font-semibold text-gray-400 dark:text-gray-500">{title}</p>
      {data.length > 0 ? <div className="h-40">{children}</div> : <p className="py-8 text-center text-sm text-gray-400 dark:text-gray-500">{resolvedEmptyText}</p>}
    </section>
  );
}

function CommonTooltip() {
  return <RechartsTooltip contentStyle={{ border: '1px solid #E5E7EB', borderRadius: 12, fontSize: 12 }} />;
}

export function BarMetricChart(props: ChartCardProps) {
  return (
    <ChartCard {...props}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={props.data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#EEF2F7" />
          <XAxis dataKey="label" stroke="#9CA3AF" fontSize={10} />
          <YAxis stroke="#9CA3AF" fontSize={10} width={36} />
          <CommonTooltip />
          <Bar dataKey="value" fill="#2563EB" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function LineMetricChart(props: ChartCardProps) {
  return (
    <ChartCard {...props}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={props.data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#EEF2F7" />
          <XAxis dataKey="label" stroke="#9CA3AF" fontSize={10} />
          <YAxis stroke="#9CA3AF" fontSize={10} width={36} />
          <CommonTooltip />
          <Line type="monotone" dataKey="value" stroke="#2563EB" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function AreaMetricChart(props: ChartCardProps) {
  return (
    <ChartCard {...props}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={props.data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#EEF2F7" />
          <XAxis dataKey="label" stroke="#9CA3AF" fontSize={10} />
          <YAxis stroke="#9CA3AF" fontSize={10} width={36} />
          <CommonTooltip />
          <Area type="monotone" dataKey="value" stroke="#0891B2" fill="#CFFAFE" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function PieMetricChart(props: ChartCardProps) {
  return (
    <ChartCard {...props}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={props.data} dataKey="value" nameKey="label" innerRadius={36} outerRadius={64} paddingAngle={3}>
            {props.data.map((point, index) => (
              <Cell key={point.label} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <CommonTooltip />
        </PieChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
