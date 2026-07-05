import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { PlanComparePage } from '@/pages/PlanComparePage';
import { renderWithProviders } from '@/test/renderWithProviders';
import { usePlansQuery } from '@/hooks/usePlanQueries';
import type { PlanListResponse } from '@/lib/api-schemas';

vi.mock('@/hooks/usePlanQueries', () => ({
  usePlansQuery: vi.fn(),
}));

const mockedUsePlansQuery = vi.mocked(usePlansQuery);

const plans: PlanListResponse = {
  total: 1,
  plans: [
    {
      id: 'plan-1',
      name: '方案 A',
      rush: [{ university: 'A', major: 'CS', estScore: 630, probability: 20, risk: '高', riskType: 'score', reason: 'gap' }],
      stable: [],
      safe: [],
      createdAt: '2026-07-04T00:00:00.000Z',
    },
  ],
};

describe('PlanComparePage i18n', () => {
  it('renders the comparison table in Chinese', () => {
    mockedUsePlansQuery.mockReturnValue({ data: plans, isLoading: false, error: null } as unknown as ReturnType<typeof usePlansQuery>);

    renderWithProviders(<PlanComparePage />);

    expect(screen.getByRole('heading', { name: '⚖️ 方案对比' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '冲刺' })).toBeInTheDocument();
    expect(screen.getByText('方案 A')).toBeInTheDocument();
  });

  it('renders the empty state in English', () => {
    mockedUsePlansQuery.mockReturnValue({ data: { plans: [], total: 0 }, isLoading: false, error: null } as unknown as ReturnType<typeof usePlansQuery>);

    renderWithProviders(<PlanComparePage />, { locale: 'en-US' });

    expect(screen.getByRole('heading', { name: 'No comparable plans yet' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Generate a plan in chat' })).toHaveAttribute('href', '/');
  });

  it('shows a safe error message without leaking backend text', () => {
    mockedUsePlansQuery.mockReturnValue({ data: undefined, isLoading: false, error: new Error('raw backend stack trace') } as unknown as ReturnType<typeof usePlansQuery>);

    renderWithProviders(<PlanComparePage />);

    expect(screen.getByRole('alert')).toHaveTextContent('方案对比数据加载失败，请稍后重试。');
    expect(screen.queryByText('raw backend stack trace')).not.toBeInTheDocument();
  });
  it('includes dark mode comparison table surfaces', () => {
    mockedUsePlansQuery.mockReturnValue({ data: plans, isLoading: false, error: null } as unknown as ReturnType<typeof usePlansQuery>);

    renderWithProviders(<PlanComparePage />, { locale: 'en-US' });

    expect(screen.getByRole('heading', { name: '⚖️ Plan comparison' })).toHaveClass('dark:text-gray-100');
    expect(screen.getByRole('link', { name: '📋 My plans' })).toHaveClass('dark:border-gray-700', 'dark:text-gray-300');
    expect(screen.getByRole('table').closest('div')).toHaveClass('dark:border-gray-800', 'dark:bg-gray-900');
    expect(screen.getByRole('columnheader', { name: 'Plan' }).closest('thead')).toHaveClass('dark:bg-gray-800', 'dark:text-gray-300');
    expect(screen.getByText('方案 A')).toHaveClass('dark:text-gray-100');
  });
});
