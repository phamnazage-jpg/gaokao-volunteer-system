import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/renderWithProviders';
import { DataQueryResult } from './DataQueryResult';

describe('DataQueryResult', () => {
  it('renders score line table and chart', () => {
    renderWithProviders(
      <DataQueryResult
        scoreLine={{
          province: '广东',
          year: 2025,
          scoreType: 'physics',
          lines: [{ batch: '本科批', score: 435, rank: 185000 }],
        }}
      />,
    );

    expect(screen.getByRole('region', { name: '分数线查询结果' })).toBeInTheDocument();
    expect(screen.getByText('2025 年分数线')).toHaveClass('sr-only');
    expect(screen.getByRole('img', { name: '批次分数线柱状图' })).toBeInTheDocument();
  });

  it('renders score line table and chart with English labels', () => {
    renderWithProviders(
      <DataQueryResult
        scoreLine={{
          province: 'Guangdong',
          year: 2025,
          scoreType: 'physics',
          lines: [{ batch: 'Undergraduate', score: 435, rank: 185000 }],
        }}
      />,
      { locale: 'en-US' },
    );

    expect(screen.getByRole('region', { name: 'Score-line query result' })).toBeInTheDocument();
    expect(screen.getByText('2025 score lines')).toHaveClass('sr-only');
    expect(screen.getByRole('img', { name: 'Batch score-line bar chart' })).toBeInTheDocument();
  });

  it('renders rank estimator result', () => {
    renderWithProviders(
      <DataQueryResult
        rankEstimator={{
          province: '广东',
          year: 2025,
          scoreType: 'physics',
          rank: 12500,
          equivalentScore: 621,
        }}
      />,
    );

    expect(screen.getByRole('region', { name: '位次估算结果' })).toHaveTextContent('621');
  });

  it('renders rank estimator result with English labels', () => {
    renderWithProviders(
      <DataQueryResult
        rankEstimator={{
          province: 'Guangdong',
          year: 2025,
          scoreType: 'physics',
          rank: 12500,
          equivalentScore: 621,
        }}
      />,
      { locale: 'en-US' },
    );

    expect(screen.getByRole('region', { name: 'Rank estimate result' })).toHaveTextContent('621');
    expect(screen.getByText('Equivalent score')).toBeInTheDocument();
  });

  it('renders major results', () => {
    renderWithProviders(<DataQueryResult majors={{ total: 1, majors: [{ id: 'm1', name: '计算机科学与技术', category: '工学' }] }} />);

    expect(screen.getByRole('region', { name: '专业查询结果' })).toBeInTheDocument();
    expect(screen.getByText('专业查询结果，共 1 条')).toHaveClass('sr-only');
    expect(screen.getByText('计算机科学与技术')).toBeInTheDocument();
  });

  it('renders major results with English labels', () => {
    renderWithProviders(<DataQueryResult majors={{ total: 1, majors: [{ id: 'm1', name: 'Computer Science', category: 'Engineering' }] }} />, { locale: 'en-US' });

    expect(screen.getByRole('region', { name: 'Major query result' })).toBeInTheDocument();
    expect(screen.getByText('Major query result, 1 total')).toHaveClass('sr-only');
    expect(screen.getByText('Computer Science')).toBeInTheDocument();
  });

  it('renders school results with tags', () => {
    renderWithProviders(<DataQueryResult schools={{ total: 1, schools: [{ id: 's1', name: '中山大学', province: '广东', is985: true, is211: true }] }} />);

    expect(screen.getByRole('region', { name: '院校查询结果' })).toBeInTheDocument();
    expect(screen.getByText('中山大学')).toBeInTheDocument();
    expect(screen.getByText('985 / 211')).toBeInTheDocument();
  });

  it('renders school results fallback tag with English labels', () => {
    renderWithProviders(<DataQueryResult schools={{ total: 1, schools: [{ id: 's1', name: 'Local College', province: 'Guangdong', is985: false, is211: false }] }} />, { locale: 'en-US' });

    expect(screen.getByRole('region', { name: 'School query result' })).toBeInTheDocument();
    expect(screen.getByText('School query result, 1 total')).toHaveClass('sr-only');
    expect(screen.getByText('Regular undergraduate')).toBeInTheDocument();
  });
});
