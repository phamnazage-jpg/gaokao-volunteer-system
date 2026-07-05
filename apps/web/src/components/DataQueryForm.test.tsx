import { describe, expect, it, vi } from 'vitest';
import { screen, within } from '@testing-library/react';
import { renderWithProviders } from '@/test/renderWithProviders';
import { DataQueryForm, type DataQueryFormValues } from './DataQueryForm';

const BASE_VALUES: DataQueryFormValues = {
  province: '广东',
  year: 2025,
  scoreType: 'physics',
  rank: 12500,
  keyword: '',
};

describe('DataQueryForm', () => {
  it('renders score line fields', () => {
    renderWithProviders(<DataQueryForm variant="scoreLine" values={BASE_VALUES} onChange={vi.fn()} />);

    expect(screen.getByRole('region', { name: '分数线查询' })).toBeInTheDocument();
    expect(screen.getByDisplayValue('广东')).toBeInTheDocument();
    expect(screen.getByDisplayValue('2025')).toBeInTheDocument();
    expect(screen.getByLabelText('选择科类')).toHaveValue('physics');
  });

  it('renders score line fields with English labels', () => {
    renderWithProviders(<DataQueryForm variant="scoreLine" values={{ ...BASE_VALUES, province: 'Guangdong' }} onChange={vi.fn()} />, { locale: 'en-US' });

    expect(screen.getByRole('region', { name: 'Score-line query' })).toBeInTheDocument();
    expect(screen.getByDisplayValue('Guangdong')).toBeInTheDocument();
    expect(screen.getByLabelText('Select subject type')).toHaveValue('physics');
    expect(screen.getByLabelText('Province help')).toBeInTheDocument();
  });

  it('renders rank estimator fields and emits numeric rank changes', async () => {
    const handleChange = vi.fn();
    const { user } = renderWithProviders(<DataQueryForm variant="rankEstimator" values={BASE_VALUES} onChange={handleChange} />);
    const rankInput = screen.getByRole('spinbutton', { name: '位次' });

    await user.clear(rankInput);
    await user.type(rankInput, '9800');

    expect(handleChange).toHaveBeenCalledWith({ rank: 125009 });
  });

  it('renders major search variant', async () => {
    const handleChange = vi.fn();
    const { user } = renderWithProviders(<DataQueryForm variant="majors" values={BASE_VALUES} onChange={handleChange} />);

    await user.type(screen.getByPlaceholderText('搜索专业、类别或培养方向…'), '计算机');

    expect(screen.getByRole('region', { name: '专业库查询' })).toBeInTheDocument();
    expect(handleChange).toHaveBeenCalledWith({ keyword: '计' });
  });

  it('renders major search variant with English labels', async () => {
    const handleChange = vi.fn();
    const { user } = renderWithProviders(<DataQueryForm variant="majors" values={BASE_VALUES} onChange={handleChange} />, { locale: 'en-US' });

    await user.type(screen.getByPlaceholderText('Search major, category, or training direction…'), 'CS');

    expect(screen.getByRole('region', { name: 'Major database' })).toBeInTheDocument();
    expect(handleChange).toHaveBeenCalledWith({ keyword: 'C' });
  });

  it('renders school search variant', () => {
    renderWithProviders(<DataQueryForm variant="schools" values={BASE_VALUES} onChange={vi.fn()} />);

    expect(screen.getByRole('region', { name: '院校库查询' })).toBeInTheDocument();
    const schoolsForm = screen.getByRole('region', { name: '院校库查询' });
    expect(within(schoolsForm).getByPlaceholderText('搜索院校、省份或 985/211…')).toBeInTheDocument();
    expect(within(schoolsForm).getByLabelText('关键词说明')).toBeInTheDocument();
  });

  it('renders school search variant with English labels', () => {
    renderWithProviders(<DataQueryForm variant="schools" values={BASE_VALUES} onChange={vi.fn()} />, { locale: 'en-US' });

    expect(screen.getByRole('region', { name: 'School database' })).toBeInTheDocument();
    const schoolsForm = screen.getByRole('region', { name: 'School database' });
    expect(within(schoolsForm).getByPlaceholderText('Search school, province, or 985/211…')).toBeInTheDocument();
    expect(within(schoolsForm).getByLabelText('Keyword help')).toBeInTheDocument();
  });
});
