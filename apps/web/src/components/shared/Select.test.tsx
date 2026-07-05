import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { Select, type SelectOption } from './Select';
import { renderWithProviders } from '@/test/renderWithProviders';

const options: SelectOption<'physics' | 'history'>[] = [
  { value: 'physics', label: '物理' },
  { value: 'history', label: '历史' },
];

describe('Select', () => {
  it('renders label, options and help text', () => {
    renderWithProviders(<Select label="选择科类" value="physics" options={options} onChange={vi.fn()} helpText="切换后刷新数据。" />);

    expect(screen.getByLabelText('选择科类')).toHaveValue('physics');
    expect(screen.getByText('切换后刷新数据。')).toBeInTheDocument();
  });

  it('emits typed option value on change', async () => {
    const onChange = vi.fn();
    const { user } = renderWithProviders(<Select label="选择科类" value="physics" options={options} onChange={onChange} />);

    await user.selectOptions(screen.getByLabelText('选择科类'), 'history');

    expect(onChange).toHaveBeenCalledWith('history');
  });
  it('includes dark mode select surfaces', () => {
    renderWithProviders(
      <Select label="Subject type" value="physics" options={options} onChange={vi.fn()} helpText="Refreshes the data after switching." />,
    );

    expect(screen.getByText('Subject type')).toHaveClass('dark:text-gray-400');
    expect(screen.getByLabelText('Subject type')).toHaveClass('dark:border-gray-700', 'dark:bg-gray-900', 'dark:text-gray-100');
    expect(screen.getByText('Refreshes the data after switching.')).toHaveClass('dark:text-gray-500');
  });
});
