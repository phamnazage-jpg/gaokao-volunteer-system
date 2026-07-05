import { describe, expect, it, vi } from 'vitest';
import { screen, within } from '@testing-library/react';
import { DataQueryPage } from './DataQueryPage';
import { renderWithProviders } from '@/test/renderWithProviders';
import { useMajorsQuery, useRankEstimatorQuery, useSchoolsQuery, useScoreLineQuery } from '@/hooks/useDataQuery';

vi.mock('@/hooks/useDataQuery', () => ({
  useScoreLineQuery: vi.fn(),
  useRankEstimatorQuery: vi.fn(),
  useMajorsQuery: vi.fn(),
  useSchoolsQuery: vi.fn(),
}));

const mockedUseScoreLineQuery = vi.mocked(useScoreLineQuery);
const mockedUseRankEstimatorQuery = vi.mocked(useRankEstimatorQuery);
const mockedUseMajorsQuery = vi.mocked(useMajorsQuery);
const mockedUseSchoolsQuery = vi.mocked(useSchoolsQuery);

describe('DataQueryPage', () => {
  it('keeps all filters before the result overview', () => {
    mockedUseScoreLineQuery.mockReturnValue({ data: undefined, isLoading: false, isError: false } as ReturnType<typeof useScoreLineQuery>);
    mockedUseRankEstimatorQuery.mockReturnValue({ data: undefined, isLoading: false, isError: false } as ReturnType<typeof useRankEstimatorQuery>);
    mockedUseMajorsQuery.mockReturnValue({ data: { majors: [], total: 0 }, isLoading: false, isError: false } as unknown as ReturnType<typeof useMajorsQuery>);
    mockedUseSchoolsQuery.mockReturnValue({ data: { schools: [], total: 0 }, isLoading: false, isError: false } as unknown as ReturnType<typeof useSchoolsQuery>);

    renderWithProviders(<DataQueryPage />);

    const schoolsForm = screen.getByRole('region', { name: '院校库查询' });
    const resultOverview = screen.getByRole('heading', { name: '查询结果' });

    expect(schoolsForm.compareDocumentPosition(resultOverview) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('renders loading and error states for result groups', () => {
    mockedUseScoreLineQuery.mockReturnValue({ data: undefined, isLoading: true, isError: false } as ReturnType<typeof useScoreLineQuery>);
    mockedUseRankEstimatorQuery.mockReturnValue({ data: undefined, isLoading: false, isError: true } as ReturnType<typeof useRankEstimatorQuery>);
    mockedUseMajorsQuery.mockReturnValue({ data: undefined, isLoading: false, isError: false } as unknown as ReturnType<typeof useMajorsQuery>);
    mockedUseSchoolsQuery.mockReturnValue({ data: undefined, isLoading: true, isError: false } as unknown as ReturnType<typeof useSchoolsQuery>);

    renderWithProviders(<DataQueryPage />);

    expect(screen.getByText('分数线加载中...')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('位次估算加载失败，请稍后重试。');
    expect(screen.getByText('专业暂无可展示结果。')).toBeInTheDocument();
    expect(screen.getByText('院校加载中...')).toBeInTheDocument();
  });

  it('renders field help tooltips', () => {
    mockedUseScoreLineQuery.mockReturnValue({ data: undefined } as ReturnType<typeof useScoreLineQuery>);
    mockedUseRankEstimatorQuery.mockReturnValue({ data: undefined } as ReturnType<typeof useRankEstimatorQuery>);
    mockedUseMajorsQuery.mockReturnValue({ data: { majors: [] } } as unknown as ReturnType<typeof useMajorsQuery>);
    mockedUseSchoolsQuery.mockReturnValue({ data: { schools: [] } } as unknown as ReturnType<typeof useSchoolsQuery>);

    renderWithProviders(<DataQueryPage />);
    const scoreLineForm = screen.getByRole('region', { name: '分数线查询' });
    const rankEstimatorForm = screen.getByRole('region', { name: '位次估算' });

    expect(within(scoreLineForm).getByLabelText('省份说明')).toBeInTheDocument();
    expect(within(scoreLineForm).getByText('用于匹配对应省份的分数线、位次和院校数据。')).toBeInTheDocument();
    expect(within(rankEstimatorForm).getByLabelText('位次说明')).toBeInTheDocument();
    expect(within(rankEstimatorForm).getByText('位次比裸分更适合跨年份比较，可用于估算等效分数。')).toBeInTheDocument();
  });

  it('renders score line chart when score line data exists', () => {
    mockedUseScoreLineQuery.mockReturnValue({
      data: {
        province: '广东',
        year: 2025,
        scoreType: 'physics',
        lines: [{ batch: '本科批', score: 435, rank: 185000 }],
      },
    } as unknown as ReturnType<typeof useScoreLineQuery>);
    mockedUseRankEstimatorQuery.mockReturnValue({ data: undefined } as ReturnType<typeof useRankEstimatorQuery>);
    mockedUseMajorsQuery.mockReturnValue({ data: { majors: [] } } as unknown as ReturnType<typeof useMajorsQuery>);
    mockedUseSchoolsQuery.mockReturnValue({ data: { schools: [] } } as unknown as ReturnType<typeof useSchoolsQuery>);

    renderWithProviders(<DataQueryPage />);

    expect(screen.getByRole('img', { name: '批次分数线柱状图' })).toBeInTheDocument();
    expect(screen.getByText('2025 年分数线')).toHaveClass('sr-only');
  });

  it('opens methodology modal from header action', async () => {
    mockedUseScoreLineQuery.mockReturnValue({ data: undefined } as ReturnType<typeof useScoreLineQuery>);
    mockedUseRankEstimatorQuery.mockReturnValue({ data: undefined } as ReturnType<typeof useRankEstimatorQuery>);
    mockedUseMajorsQuery.mockReturnValue({ data: { majors: [] } } as unknown as ReturnType<typeof useMajorsQuery>);
    mockedUseSchoolsQuery.mockReturnValue({ data: { schools: [] } } as unknown as ReturnType<typeof useSchoolsQuery>);

    const { user } = renderWithProviders(<DataQueryPage />);

    await user.click(screen.getByRole('button', { name: '查看数据口径' }));

    expect(screen.getByRole('dialog', { name: '数据查询口径' })).toHaveTextContent('位次估算');
  });

  it('renders methodology and score type controls with English labels', async () => {
    mockedUseScoreLineQuery.mockReturnValue({ data: undefined } as ReturnType<typeof useScoreLineQuery>);
    mockedUseRankEstimatorQuery.mockReturnValue({ data: undefined } as ReturnType<typeof useRankEstimatorQuery>);
    mockedUseMajorsQuery.mockReturnValue({ data: { majors: [] } } as unknown as ReturnType<typeof useMajorsQuery>);
    mockedUseSchoolsQuery.mockReturnValue({ data: { schools: [] } } as unknown as ReturnType<typeof useSchoolsQuery>);

    const { user } = renderWithProviders(<DataQueryPage />, { locale: 'en-US' });
    const scoreLineForm = screen.getByRole('region', { name: 'Score-line query' });

    expect(screen.getByRole('heading', { name: 'Data query' })).toBeInTheDocument();
    expect(within(scoreLineForm).getByLabelText('Select subject type')).toHaveValue('physics');

    await user.click(screen.getByRole('button', { name: 'View data methodology' }));

    expect(screen.getByRole('dialog', { name: 'Data query methodology' })).toHaveTextContent('Rank estimate');
  });

  it('uses enhanced select for score type changes', async () => {
    mockedUseScoreLineQuery.mockReturnValue({ data: undefined } as ReturnType<typeof useScoreLineQuery>);
    mockedUseRankEstimatorQuery.mockReturnValue({ data: undefined } as ReturnType<typeof useRankEstimatorQuery>);
    mockedUseMajorsQuery.mockReturnValue({ data: { majors: [] } } as unknown as ReturnType<typeof useMajorsQuery>);
    mockedUseSchoolsQuery.mockReturnValue({ data: { schools: [] } } as unknown as ReturnType<typeof useSchoolsQuery>);

    const { user } = renderWithProviders(<DataQueryPage />);
    const scoreLineForm = screen.getByRole('region', { name: '分数线查询' });
    const scoreTypeSelect = within(scoreLineForm).getByLabelText('选择科类');

    await user.selectOptions(scoreTypeSelect, 'history');

    expect(scoreTypeSelect).toHaveValue('history');
  });
  it('includes dark mode page header and methodology styles', async () => {
    mockedUseScoreLineQuery.mockReturnValue({ data: undefined } as ReturnType<typeof useScoreLineQuery>);
    mockedUseRankEstimatorQuery.mockReturnValue({ data: undefined } as ReturnType<typeof useRankEstimatorQuery>);
    mockedUseMajorsQuery.mockReturnValue({ data: { majors: [] } } as unknown as ReturnType<typeof useMajorsQuery>);
    mockedUseSchoolsQuery.mockReturnValue({ data: { schools: [] } } as unknown as ReturnType<typeof useSchoolsQuery>);

    const { user } = renderWithProviders(<DataQueryPage />, { locale: 'en-US' });

    expect(screen.getByRole('heading', { name: 'Data query' })).toHaveClass('dark:text-gray-100');
    expect(screen.getByRole('button', { name: 'View data methodology' })).toHaveClass('dark:border-blue-500/30', 'dark:bg-blue-500/10');

    await user.click(screen.getByRole('button', { name: 'View data methodology' }));

    expect(screen.getByText('Score lines:')).toHaveClass('dark:text-gray-100');
  });
});
