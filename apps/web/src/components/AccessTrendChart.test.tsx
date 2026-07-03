/**
 * V10 · Sprint 3 · AccessTrendChart 单测
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AccessTrendChart } from './AccessTrendChart';

describe('AccessTrendChart', () => {
  it('renders without crashing with empty data', () => {
    render(<AccessTrendChart data={[]} />);
    expect(screen.getByLabelText('访问趋势')).toBeInTheDocument();
  });

  it('renders with sample data', () => {
    render(
      <AccessTrendChart
        data={[
          { date: '07-01', views: 3 },
          { date: '07-02', views: 7 },
        ]}
      />,
    );
    // Recharts ResponsiveContainer 在 jsdom 下需要 layout 才能生成 svg
    expect(screen.getByLabelText('访问趋势')).toBeInTheDocument();
  });
});