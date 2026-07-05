import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { AreaMetricChart, BarMetricChart, LineMetricChart, PieMetricChart } from './Charts';
import { renderWithProviders } from '@/test/renderWithProviders';

const data = [
  { label: '本科批', value: 435 },
  { label: '专科批', value: 180 },
];

describe('Charts', () => {
  it('renders bar chart container with accessible label', () => {
    renderWithProviders(<BarMetricChart title="批次分数线图" ariaLabel="批次分数线柱状图" data={data} />);

    expect(screen.getByRole('img', { name: '批次分数线柱状图' })).toBeInTheDocument();
    expect(screen.getByText('批次分数线图')).toBeInTheDocument();
  });

  it('renders localized empty state when chart data is empty', () => {
    renderWithProviders(<LineMetricChart title="趋势图" ariaLabel="趋势折线图" data={[]} />);

    expect(screen.getByRole('img', { name: '趋势折线图' })).toHaveTextContent('暂无图表数据');
  });

  it('renders English empty state', () => {
    renderWithProviders(<LineMetricChart title="Trend" ariaLabel="Trend line chart" data={[]} />, { locale: 'en-US' });

    expect(screen.getByRole('img', { name: 'Trend line chart' })).toHaveTextContent('No chart data');
  });

  it('renders all supported chart variants', () => {
    renderWithProviders(
      <div>
        <LineMetricChart title="折线" ariaLabel="折线图" data={data} />
        <AreaMetricChart title="面积" ariaLabel="面积图" data={data} />
        <PieMetricChart title="饼图" ariaLabel="饼图" data={data} />
      </div>,
    );

    expect(screen.getByRole('img', { name: '折线图' })).toBeInTheDocument();
    expect(screen.getByRole('img', { name: '面积图' })).toBeInTheDocument();
    expect(screen.getByRole('img', { name: '饼图' })).toBeInTheDocument();
  });
  it('includes dark mode chart surfaces', () => {
    renderWithProviders(<LineMetricChart title="Trend" ariaLabel="Trend line chart" data={[]} />, { locale: 'en-US' });

    expect(screen.getByRole('img', { name: 'Trend line chart' })).toHaveClass('dark:border-gray-800', 'dark:bg-gray-900');
    expect(screen.getByText('Trend')).toHaveClass('dark:text-gray-500');
    expect(screen.getByText('No chart data')).toHaveClass('dark:text-gray-500');
  });
});
