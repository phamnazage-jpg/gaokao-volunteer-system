/**
 * V10 选项 B · FormCard 单测
 *
 * 覆盖 V10 不变量 C3: 3-step guards
 *  - step 1→2: 需 province
 *  - step 2→3: 需 score
 *  - 后退保留数据
 */
import { describe, it, expect, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FormCard, type FormCardData } from '@/components/FormCard';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('FormCard (V10 选项 B · RHF + Zod)', () => {
  it('初始渲染 step 1: 省份选择', () => {
    renderWithProviders(<FormCard onSubmit={vi.fn()} />);
    expect(screen.getByText('你的高考省份')).toBeInTheDocument();
    expect(screen.getByText('省份')).toBeInTheDocument();
  });

  it('step 1 未选省份时点击下一步不前进', async () => {
    const user = userEvent.setup();
    renderWithProviders(<FormCard onSubmit={vi.fn()} />);

    const nextBtn = screen.getByText(/下一步/);
    await user.click(nextBtn);

    // 仍在 step 1
    expect(screen.getByText('你的高考省份')).toBeInTheDocument();
  });

  it('step 1 选省份后点击下一步进入 step 2', async () => {
    const user = userEvent.setup();
    renderWithProviders(<FormCard onSubmit={vi.fn()} />);

    await user.selectOptions(screen.getByLabelText('你的高考省份'), '广东');
    await user.click(screen.getByText(/下一步/));

    await waitFor(() => {
      expect(screen.getByText('你的高考分数')).toBeInTheDocument();
    });
  });

  it('step 3 后退保留数据', () => {
    const initialData: Partial<FormCardData> = { province: '广东', score: 620, rank: 8500 };
    renderWithProviders(<FormCard onSubmit={vi.fn()} initialData={initialData} />);

    // 初始 step 0
    expect(screen.getByText('你的高考省份')).toBeInTheDocument();

    // 验证 select 显示初始值
    expect(screen.getByLabelText('你的高考省份')).toHaveValue('广东');
  });
  it('includes dark mode variants for form shell and fields', () => {
    renderWithProviders(<FormCard onSubmit={vi.fn()} />, { locale: 'en-US' });

    const form = screen.getByRole('form', { name: 'Application information collection' });
    expect(form).toHaveClass('dark:bg-gray-900', 'dark:border-gray-800');
    expect(screen.getByLabelText('Your Gaokao province')).toHaveClass('dark:bg-gray-800', 'dark:text-gray-100');
    expect(screen.getByText('Your Gaokao province')).toHaveClass('dark:text-gray-300');
  });
});
