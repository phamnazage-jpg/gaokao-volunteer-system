import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { DatePicker } from './DatePicker';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('DatePicker', () => {
  it('renders date input with label and help text', () => {
    renderWithProviders(
      <DatePicker label="仅看此日期后更新" value="2026-07-04" onChange={vi.fn()} helpText="按最近更新时间筛选。" />,
    );

    expect(screen.getByLabelText('仅看此日期后更新')).toHaveValue('2026-07-04');
    expect(screen.getByText('按最近更新时间筛选。')).toBeInTheDocument();
  });

  it('emits selected date changes', async () => {
    const onChange = vi.fn();
    const { user } = renderWithProviders(<DatePicker label="仅看此日期后更新" value="" onChange={onChange} />);

    await user.type(screen.getByLabelText('仅看此日期后更新'), '2026-07-04');

    expect(onChange).toHaveBeenLastCalledWith('2026-07-04');
  });
  it('includes dark mode input surfaces', () => {
    renderWithProviders(<DatePicker label="Updated after" value="2026-07-04" onChange={vi.fn()} helpText="Filter by update date." />);

    expect(screen.getByText('Updated after')).toHaveClass('dark:text-gray-400');
    expect(screen.getByLabelText('Updated after')).toHaveClass('dark:border-gray-700', 'dark:bg-gray-900', 'dark:text-gray-100');
    expect(screen.getByText('Filter by update date.')).toHaveClass('dark:text-gray-500');
  });
});
