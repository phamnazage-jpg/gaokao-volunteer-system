/**
 * V10 · Sprint 3 · AccessTrendChart 单测
 */
import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { AccessTrendChart } from './AccessTrendChart';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('AccessTrendChart', () => {
  it('renders without crashing with empty data', () => {
    renderWithProviders(<AccessTrendChart data={[]} />);
    expect(screen.getByLabelText('访问趋势')).toBeInTheDocument();
  });

  it('renders with sample data', () => {
    renderWithProviders(
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

  it('renders English chart label when locale switches', () => {
    renderWithProviders(<AccessTrendChart data={[]} />, { locale: 'en-US' });

    expect(screen.getByLabelText('Access trend')).toBeInTheDocument();
  });
});

it('includes dark mode chart shell', () => {
  renderWithProviders(<AccessTrendChart data={[]} />, { locale: 'en-US' });

  expect(screen.getByRole('img', { name: 'Access trend' })).toHaveClass(
    'dark:border-gray-800',
    'dark:bg-gray-900',
  );
  expect(screen.getByText('Access trend')).toHaveClass('dark:text-gray-500');
});
