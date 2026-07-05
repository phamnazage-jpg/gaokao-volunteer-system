import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/renderWithProviders';
import { usePortalCWBQuery, usePortalFullPlanQuery } from '@/hooks/usePortal';
import { PortalPage } from './PortalPage';

vi.mock('@/hooks/usePortal', () => ({
  usePortalCWBQuery: vi.fn(),
  usePortalFullPlanQuery: vi.fn(),
}));

const mockedUsePortalCWBQuery = vi.mocked(usePortalCWBQuery);
const mockedUsePortalFullPlanQuery = vi.mocked(usePortalFullPlanQuery);

function mockPortalData() {
  mockedUsePortalCWBQuery.mockReturnValue({
    isLoading: false,
    data: {
      token: 'share-token',
      province: '广东',
      year: 2025,
      scoreType: 'physics',
      score: 620,
      rank: 12500,
      equivalentScore: 618,
    },
  } as unknown as ReturnType<typeof usePortalCWBQuery>);
  mockedUsePortalFullPlanQuery.mockReturnValue({
    isLoading: false,
    data: {
      token: 'share-token',
      plan: {
        id: 'plan-001',
        title: '广东物理 620 志愿方案',
        schools: [
          {
            id: 'school-1',
            name: '中山大学',
            majors: ['计算机类', '软件工程'],
            admissionProbability: '\u51b2',
          },
        ],
      },
      createdAt: '2026-07-04T00:00:00.000Z',
    },
  } as unknown as ReturnType<typeof usePortalFullPlanQuery>);
}

describe('PortalPage', () => {
  it('renders loading state', () => {
    mockedUsePortalCWBQuery.mockReturnValue({ isLoading: true } as ReturnType<typeof usePortalCWBQuery>);
    mockedUsePortalFullPlanQuery.mockReturnValue({ isLoading: false } as ReturnType<typeof usePortalFullPlanQuery>);

    renderWithProviders(<PortalPage />);

    expect(screen.getByText('正在加载方案…')).toBeInTheDocument();
  });

  it('renders safe error copy without backend details', () => {
    mockedUsePortalCWBQuery.mockReturnValue({
      isLoading: false,
      isError: true,
      error: new Error('raw backend stack trace'),
    } as unknown as ReturnType<typeof usePortalCWBQuery>);
    mockedUsePortalFullPlanQuery.mockReturnValue({
      isLoading: false,
      isError: false,
      data: undefined,
    } as unknown as ReturnType<typeof usePortalFullPlanQuery>);

    renderWithProviders(<PortalPage />, { locale: 'en-US' });

    expect(screen.getByRole('alert')).toHaveTextContent('Unable to load this shared plan. The link may be expired or temporarily unavailable.');
    expect(screen.queryByText(/raw backend stack trace/i)).not.toBeInTheDocument();
  });

  it('renders an empty fallback when no shared data is available', () => {
    mockedUsePortalCWBQuery.mockReturnValue({
      isLoading: false,
      isError: false,
      data: undefined,
    } as unknown as ReturnType<typeof usePortalCWBQuery>);
    mockedUsePortalFullPlanQuery.mockReturnValue({
      isLoading: false,
      isError: false,
      data: undefined,
    } as unknown as ReturnType<typeof usePortalFullPlanQuery>);

    renderWithProviders(<PortalPage />, { locale: 'en-US' });

    expect(screen.getByText('No shared plan data is available for this link.')).toBeInTheDocument();
  });

  it('renders shared portal data', () => {
    mockPortalData();

    renderWithProviders(<PortalPage />);

    expect(screen.getByRole('heading', { name: '招生门户' })).toBeInTheDocument();
    expect(screen.getByText('考生位次信息')).toBeInTheDocument();
    expect(screen.getByText('等效分数：618')).toBeInTheDocument();
    expect(screen.getByText('冲')).toBeInTheDocument();
    expect(screen.getByText('专业：计算机类、软件工程')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /前往完整方案/ })).toHaveAttribute('href', '/portal/full');
  });

  it('renders shared portal data with English chrome labels', () => {
    mockPortalData();

    renderWithProviders(<PortalPage />, { locale: 'en-US' });

    expect(screen.getByRole('heading', { name: 'Admissions portal' })).toBeInTheDocument();
    expect(screen.getByText('Candidate rank information')).toBeInTheDocument();
    expect(screen.getByText('Equivalent score: 618')).toBeInTheDocument();
    expect(screen.getByText('Reach')).toBeInTheDocument();
    expect(screen.getByText('Majors: 计算机类, 软件工程')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Open full plan/ })).toHaveAttribute('href', '/portal/full');
  });
  it('includes dark mode variants for portal cards and probability badges', () => {
    mockPortalData();

    renderWithProviders(<PortalPage />, { locale: 'en-US' });

    expect(screen.getByText('Candidate rank information').closest('div')).toHaveClass('dark:bg-gray-900');
    expect(screen.getByText('Reach')).toHaveClass('dark:bg-red-950/40', 'dark:text-red-200');
  });
});
