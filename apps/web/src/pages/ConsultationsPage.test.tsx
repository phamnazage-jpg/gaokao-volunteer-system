import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { ConsultationsPage } from './ConsultationsPage';
import { renderWithProviders } from '@/test/renderWithProviders';
import { useConsultationsQuery } from '@/hooks/useConsultationQueries';
import type { ConsultationListResponse } from '@/lib/api-schemas';

vi.mock('@/hooks/useConsultationQueries', () => ({
  useConsultationsQuery: vi.fn(),
}));

const mockedUseConsultationsQuery = vi.mocked(useConsultationsQuery);

function makeConsultations(count: number): ConsultationListResponse {
  return {
    total: count,
      consultations: Array.from({ length: count }).map((_, index) => ({
        id: `consultation-${index + 1}`,
        title: `咨询 ${index + 1}`,
        messageCount: index + 2,
        createdAt: `2026-07-${String(index + 1).padStart(2, '0')}T00:00:00.000Z`,
        updatedAt: `2026-07-${String(index + 1).padStart(2, '0')}T00:00:00.000Z`,
      })),
  };
}

describe('ConsultationsPage', () => {
  it('shows an actionable empty state when no consultations exist', async () => {
    mockedUseConsultationsQuery.mockReturnValue({
      data: { consultations: [], total: 0 },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useConsultationsQuery>);

    renderWithProviders(<ConsultationsPage />);

    expect(await screen.findByRole('heading', { name: '暂无咨询记录' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '开始咨询' })).toHaveAttribute('href', '/');
  });

  it('renders empty state in English when locale switches', async () => {
    mockedUseConsultationsQuery.mockReturnValue({
      data: { consultations: [], total: 0 },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useConsultationsQuery>);

    renderWithProviders(<ConsultationsPage />, { locale: 'en-US' });

    expect(await screen.findByRole('heading', { name: 'No consultations yet' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Start consulting' })).toHaveAttribute('href', '/');
  });

  it('shows a skeleton while loading consultations', () => {
    mockedUseConsultationsQuery.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as unknown as ReturnType<typeof useConsultationsQuery>);

    renderWithProviders(<ConsultationsPage />);
    expect(screen.getByRole('status', { name: '咨询记录加载中' })).toBeInTheDocument();
  });

  it('shows a safe error message without leaking backend text', () => {
    mockedUseConsultationsQuery.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('raw backend stack trace'),
    } as unknown as ReturnType<typeof useConsultationsQuery>);

    renderWithProviders(<ConsultationsPage />);

    expect(screen.getByRole('alert')).toHaveTextContent('咨询记录加载失败，请稍后重试。');
    expect(screen.queryByText('raw backend stack trace')).not.toBeInTheDocument();
  });

  it('paginates consultation cards locally', async () => {
    mockedUseConsultationsQuery.mockReturnValue({
      data: makeConsultations(6),
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useConsultationsQuery>);

    const { user } = renderWithProviders(<ConsultationsPage />);

    expect(screen.getByText('咨询 1')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: '咨询 1 头像' })).toBeInTheDocument();
    expect(screen.queryByText('咨询 6')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '下一页' }));

    expect(screen.getByText('咨询 6')).toBeInTheDocument();
  });

  it('filters consultations by updated date', async () => {
    mockedUseConsultationsQuery.mockReturnValue({
      data: makeConsultations(3),
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useConsultationsQuery>);

    const { user } = renderWithProviders(<ConsultationsPage />);

    await user.type(screen.getByLabelText('仅看此日期后更新'), '2026-07-03');

    expect(screen.queryByText('咨询 1')).not.toBeInTheDocument();
    expect(screen.queryByText('咨询 2')).not.toBeInTheDocument();
    expect(screen.getByText('咨询 3')).toBeInTheDocument();
  });

  it('renders the date filter label in English', () => {
    mockedUseConsultationsQuery.mockReturnValue({
      data: makeConsultations(1),
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useConsultationsQuery>);

    renderWithProviders(<ConsultationsPage />, { locale: 'en-US' });

    expect(screen.getByRole('heading', { name: '💬 Consultations' })).toBeInTheDocument();
    expect(screen.getByLabelText('Updated after')).toBeInTheDocument();
  });
  it('includes dark mode consultation list surfaces', () => {
    mockedUseConsultationsQuery.mockReturnValue({
      data: makeConsultations(1),
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useConsultationsQuery>);

    renderWithProviders(<ConsultationsPage />, { locale: 'en-US' });

    expect(screen.getByRole('heading', { name: '💬 Consultations' })).toHaveClass('dark:text-gray-100');
    expect(screen.getByText('咨询 1').closest('div')?.parentElement).toHaveClass('dark:border-gray-800', 'dark:bg-gray-900');
    expect(screen.getByText('咨询 1')).toHaveClass('dark:text-gray-100');
  });
});
