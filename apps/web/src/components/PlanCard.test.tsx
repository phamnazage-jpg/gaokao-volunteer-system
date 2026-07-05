import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/renderWithProviders';
import type { PlanCardMessageData } from '@/types/message';
import { PlanCard } from './PlanCard';

const PLAN_DATA: PlanCardMessageData = {
  type: 'plan_card',
  rush: [
    {
      university: '中山大学',
      major: '计算机类',
      estScore: 635,
      probability: 42,
      risk: '冲刺',
      riskType: 'rush',
      reason: '专业实力强，录取概率偏冲刺。',
    },
  ],
  stable: [
    {
      university: '华南师范大学',
      major: '软件工程',
      estScore: 610,
      probability: 72,
      risk: '稳妥',
      riskType: 'stable',
      reason: '分数与往年录取区间接近。',
    },
  ],
  safe: [],
};

describe('PlanCard', () => {
  it('renders plan tabs and action buttons', async () => {
    const handleSave = vi.fn();
    const handleExport = vi.fn();
    const { user } = renderWithProviders(<PlanCard data={PLAN_DATA} userScore={620} onSave={handleSave} onExport={handleExport} />);

    expect(screen.getByText('🎯 你的志愿方案')).toBeInTheDocument();
    expect(screen.getByText('基于你的 620 分生成')).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /冲刺/ })).toHaveAttribute('aria-selected', 'true');

    await user.click(screen.getByRole('button', { name: '💾 保存' }));
    await user.click(screen.getByRole('button', { name: '📤 导出' }));

    expect(handleSave).toHaveBeenCalledOnce();
    expect(handleExport).toHaveBeenCalledOnce();
  });

  it('renders English labels and empty group state', async () => {
    const { user } = renderWithProviders(<PlanCard data={PLAN_DATA} userScore={620} savedPlanId="plan-001" adjusted />, { locale: 'en-US' });

    expect(screen.getByText('🎯 Adjusted application plan')).toBeInTheDocument();
    expect(screen.getByText('Generated from your 620 score')).toBeInTheDocument();
    expect(screen.getByText('✓ Saved')).toBeInTheDocument();

    await user.click(screen.getByRole('tab', { name: /Safety/ }));

    expect(screen.getByText('No schools in this group')).toBeInTheDocument();
  });
});

it('includes dark mode plan card surfaces', () => {
  renderWithProviders(<PlanCard data={PLAN_DATA} userScore={620} savedPlanId="plan-001" adjusted />, {
    locale: 'en-US',
  });

  expect(screen.getByText('🎯 Adjusted application plan').closest('div')?.parentElement?.parentElement).toHaveClass(
    'dark:border-gray-800',
    'dark:bg-gray-900',
  );
  expect(screen.getByText('🎯 Adjusted application plan')).toHaveClass('dark:text-gray-100');
  expect(screen.getByText('Generated from your 620 score')).toHaveClass('dark:text-gray-400');
  expect(screen.getByText('✓ Saved')).toHaveClass('dark:text-green-300');
  expect(screen.getByRole('tab', { name: /Reach/ })).toHaveClass('dark:bg-orange-500/10', 'dark:text-orange-300');
});
