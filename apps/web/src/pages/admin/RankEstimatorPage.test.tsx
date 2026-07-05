import { describe, expect, it } from 'vitest';
import { screen, within } from '@testing-library/react';
import { AdminRankEstimatorPage } from './RankEstimatorPage';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('AdminRankEstimatorPage', () => {
  it('loads rank estimate through the admin entry', async () => {
    renderWithProviders(<AdminRankEstimatorPage />);

    expect(screen.getAllByRole('heading', { name: '位次估算' })).toHaveLength(2);
    expect(screen.getByRole('status')).toHaveTextContent('正在加载位次估算');
    const result = await screen.findByRole('region', { name: '位次估算结果' });
    expect(result).toHaveTextContent('621');
    expect(screen.getByText('等效分数')).toBeInTheDocument();
  });

  it('refreshes rank estimate when subject type changes', async () => {
    const { user } = renderWithProviders(<AdminRankEstimatorPage />);

    expect(await screen.findByText('621')).toBeInTheDocument();

    const form = screen.getByRole('region', { name: '位次估算' });
    await user.selectOptions(within(form).getByLabelText('选择科类'), 'history');

    expect(await screen.findByText('603')).toBeInTheDocument();
    expect(screen.queryByText('621')).not.toBeInTheDocument();
  });
});
