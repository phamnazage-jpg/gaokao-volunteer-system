import { describe, expect, it } from 'vitest';
import { screen, within } from '@testing-library/react';
import { AdminScoreLinesPage } from './ScoreLinesPage';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('AdminScoreLinesPage', () => {
  it('loads score lines through the admin entry', async () => {
    renderWithProviders(<AdminScoreLinesPage />);

    expect(screen.getAllByRole('heading', { name: '分数线查询' })).toHaveLength(2);
    expect(screen.getByRole('status')).toHaveTextContent('正在加载分数线');
    expect(await screen.findByRole('region', { name: '分数线查询结果' })).toBeInTheDocument();
    expect(screen.getAllByText('本科批')).toHaveLength(2);
    expect(screen.getAllByText('特殊类型招生控制线')).toHaveLength(2);
    expect(screen.getByRole('img', { name: '批次分数线柱状图' })).toBeInTheDocument();
  });

  it('refreshes score lines when subject type changes', async () => {
    const { user } = renderWithProviders(<AdminScoreLinesPage />);

    expect(await screen.findByText('435')).toBeInTheDocument();

    const form = screen.getByRole('region', { name: '分数线查询' });
    await user.selectOptions(within(form).getByLabelText('选择科类'), 'history');

    expect(await screen.findByText('428')).toBeInTheDocument();
    expect(screen.queryByText('435')).not.toBeInTheDocument();
  });
});
