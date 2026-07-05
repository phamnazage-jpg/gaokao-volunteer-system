import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/renderWithProviders';
import { AuditReportCard } from './AuditReportCard';

const HIGH_RISK = '\u9ad8';

describe('AuditReportCard', () => {
  it('renders report score and risk action', async () => {
    const handleFix = vi.fn();
    const { user } = renderWithProviders(
      <AuditReportCard
        savedPlanId="plan-abcdef"
        onFixRequest={handleFix}
        data={{
          type: 'audit_report',
          score: 72,
          risks: [{ index: 1, level: HIGH_RISK, title: '保底不足', description: '建议增加保底院校。' }],
        }}
      />,
    );

    expect(screen.getByText('📋 方案审核报告')).toBeInTheDocument();
    expect(screen.getByLabelText('审核分数 72')).toBeInTheDocument();
    expect(screen.getByText('高风险')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '一键修复' }));

    expect(handleFix).toHaveBeenCalledWith(1, '保底不足');
  });

  it('renders empty report with English labels', () => {
    renderWithProviders(
      <AuditReportCard
        savedPlanId="plan-abcdef"
        data={{
          type: 'audit_report',
          score: 92,
          risks: [],
        }}
      />,
      { locale: 'en-US' },
    );

    expect(screen.getByText('📋 Plan review report')).toBeInTheDocument();
    expect(screen.getByText('Plan #plan-a')).toBeInTheDocument();
    expect(screen.getByLabelText('Review score 92')).toBeInTheDocument();
    expect(screen.getByText('🎉 No risks found. This plan looks stable.')).toBeInTheDocument();
  });
});
