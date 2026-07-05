import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import { PlanDetailPage } from '@/pages/PlanDetailPage';
import { renderWithProviders } from '@/test/renderWithProviders';
import { usePlanQuery } from '@/hooks/usePlanQueries';

vi.mock('@/hooks/usePlanQueries', () => ({
  usePlanQuery: vi.fn(),
}));

const mockedUsePlanQuery = vi.mocked(usePlanQuery);

function renderPage(locale: 'zh-CN' | 'en-US' = 'zh-CN') {
  return renderWithProviders(
    <Routes>
      <Route path="/" element={<PlanDetailPage />} />
    </Routes>,
    { locale },
  );
}

describe('PlanDetailPage i18n', () => {
  it('renders grouped counts in Chinese', () => {
    mockedUsePlanQuery.mockReturnValue({
      data: { id: 'plan-1', name: '方案 A', rush: [], stable: [], safe: [], createdAt: '2026-07-04T00:00:00.000Z' },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof usePlanQuery>);

    renderPage();

    expect(screen.getByRole('heading', { name: '方案 A' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: '🚀 冲刺 (0)' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: '🎯 稳妥 (0)' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: '🛡️ 保底 (0)' })).toBeInTheDocument();
  });

  it('renders not-found state in English', () => {
    mockedUsePlanQuery.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof usePlanQuery>);

    renderPage('en-US');

    expect(screen.getByText('Plan does not exist')).toHaveClass('dark:text-gray-400');
  });

  it('renders loading and content with dark mode surfaces', () => {
    mockedUsePlanQuery.mockReturnValueOnce({
      data: undefined,
      isLoading: true,
      error: null,
    } as unknown as ReturnType<typeof usePlanQuery>);

    const { rerender } = renderPage('en-US');

    expect(screen.getByText('Loading...')).toHaveClass('dark:text-gray-400');

    mockedUsePlanQuery.mockReturnValue({
      data: { id: 'plan-1', name: 'Plan A', rush: [], stable: [], safe: [], createdAt: '2026-07-04T00:00:00.000Z' },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof usePlanQuery>);

    rerender(
      <Routes>
        <Route path="/" element={<PlanDetailPage />} />
      </Routes>,
    );

    expect(screen.getByRole('heading', { name: 'Plan A' }).parentElement).toHaveClass('dark:text-gray-100');
  });

  it('shows a safe error message without leaking backend text', () => {
    mockedUsePlanQuery.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('raw backend stack trace'),
    } as unknown as ReturnType<typeof usePlanQuery>);

    renderPage();

    expect(screen.getByRole('alert')).toHaveTextContent('方案详情加载失败，请返回列表后重试。');
    expect(screen.queryByText('raw backend stack trace')).not.toBeInTheDocument();
  });
});
