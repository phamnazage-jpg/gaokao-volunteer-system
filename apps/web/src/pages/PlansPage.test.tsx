import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { PlansPage } from './PlansPage';
import { renderWithProviders } from '@/test/renderWithProviders';
import { usePlansQuery } from '@/hooks/usePlanQueries';
import type { PlanListResponse } from '@/lib/api-schemas';

vi.mock('@/hooks/usePlanQueries', () => ({
  usePlansQuery: vi.fn(),
}));

const mockedUsePlansQuery = vi.mocked(usePlansQuery);

function makePlans(count: number): PlanListResponse {
  return {
    total: count,
    plans: Array.from({ length: count }).map((_, index) => ({
      id: `plan-${index + 1}`,
      name: `方案 ${index + 1}`,
      rush: [],
      stable: [],
      safe: [],
      createdAt: '2026-07-04T00:00:00.000Z',
    })),
  };
}

describe('PlansPage', () => {
  it('shows an actionable empty state when no plans exist', async () => {
    mockedUsePlansQuery.mockReturnValue({
      data: { plans: [], total: 0 },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof usePlansQuery>);

    renderWithProviders(<PlansPage />);

    expect(await screen.findByRole('heading', { name: '暂无方案' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '去对话页生成方案' })).toHaveAttribute('href', '/');
  });

  it('renders empty state in English when locale switches', async () => {
    mockedUsePlansQuery.mockReturnValue({
      data: { plans: [], total: 0 },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof usePlansQuery>);

    renderWithProviders(<PlansPage />, { locale: 'en-US' });

    expect(await screen.findByRole('heading', { name: 'No plans yet' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Generate a plan in chat' })).toHaveAttribute('href', '/');
  });

  it('shows a skeleton while loading plans', () => {
    mockedUsePlansQuery.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as unknown as ReturnType<typeof usePlansQuery>);

    renderWithProviders(<PlansPage />);
    expect(screen.getByRole('status', { name: '方案列表加载中' })).toBeInTheDocument();
  });

  it('shows a safe error message without leaking backend text', () => {
    mockedUsePlansQuery.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('raw backend stack trace'),
    } as unknown as ReturnType<typeof usePlansQuery>);

    renderWithProviders(<PlansPage />);

    expect(screen.getByRole('alert')).toHaveTextContent('方案列表加载失败，请稍后重试。');
    expect(screen.queryByText('raw backend stack trace')).not.toBeInTheDocument();
  });

  it('paginates plan cards locally', async () => {
    mockedUsePlansQuery.mockReturnValue({
      data: makePlans(6),
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof usePlansQuery>);

    const { user } = renderWithProviders(<PlansPage />);

    expect(screen.getByText('方案 1')).toBeInTheDocument();
    expect(screen.queryByText('方案 6')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '下一页' }));

    expect(screen.getByText('方案 6')).toBeInTheDocument();
  });
  it('includes dark mode plan list surfaces', () => {
    mockedUsePlansQuery.mockReturnValue({
      data: makePlans(1),
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof usePlansQuery>);

    renderWithProviders(<PlansPage />, { locale: 'en-US' });

    expect(screen.getByRole('heading', { name: '📋 My plans' })).toHaveClass('dark:text-gray-100');
    expect(screen.getByText('方案 1').closest('a')).toHaveClass('dark:border-gray-800', 'dark:bg-gray-900');
    expect(screen.getByText('方案 1')).toHaveClass('dark:text-gray-100');
  });
});
