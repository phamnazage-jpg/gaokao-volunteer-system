import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/renderWithProviders';
import type { CareerCardMessageData } from '@/types/message';
import { CareerCard } from './CareerCard';

const GOOD_PROSPECT = '\u597d';
const MEDIUM_PROSPECT = '\u4e2d';
const POOR_PROSPECT = '\u5dee';

const CAREER_DATA: CareerCardMessageData = {
  type: 'career_card',
  careers: [
    { name: 'AI 工程师', description: '负责模型应用落地。', salary: '25-45k', prospect: GOOD_PROSPECT },
    { name: '数据分析师', description: '负责业务数据分析。', salary: '18-30k', prospect: MEDIUM_PROSPECT },
    { name: '测试工程师', description: '负责质量保障。', salary: '12-20k', prospect: MEDIUM_PROSPECT },
    { name: '传统录入员', description: '自动化替代风险高。', salary: '6-8k', prospect: POOR_PROSPECT },
  ],
};

describe('CareerCard', () => {
  it('renders recommendations and expands remaining careers', async () => {
    const { user } = renderWithProviders(<CareerCard data={CAREER_DATA} />);

    expect(screen.getByText('💼 相关职业推荐')).toBeInTheDocument();
    expect(screen.getByText('前景好')).toBeInTheDocument();
    expect(screen.queryByText('传统录入员')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '展开剩余 1 个职业' }));

    expect(screen.getByText('传统录入员')).toBeInTheDocument();
    expect(screen.getByText('前景较差')).toBeInTheDocument();
  });

  it('renders English labels', async () => {
    const { user } = renderWithProviders(<CareerCard data={CAREER_DATA} />, { locale: 'en-US' });

    expect(screen.getByText('💼 Related career recommendations')).toBeInTheDocument();
    expect(screen.getByText('Strong outlook')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Expand remaining 1 careers' }));

    expect(screen.getByText('Weak outlook')).toBeInTheDocument();
  });
});
