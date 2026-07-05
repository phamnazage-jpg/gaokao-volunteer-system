import { describe, expect, it } from 'vitest';
import { screen, within } from '@testing-library/react';
import { AdminShareLinksPage } from './ShareLinksPage';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('AdminShareLinksPage', () => {
  it('loads admin share links with access metrics', async () => {
    renderWithProviders(<AdminShareLinksPage />);

    expect(screen.getByRole('status')).toHaveTextContent('正在加载分享链接');
    expect(await screen.findByText('ABC123')).toBeInTheDocument();
    expect(screen.getByText('RPT456')).toBeInTheDocument();
    expect(screen.getByText('example.test/s/ABC123')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();

    const table = screen.getByRole('region', { name: '分享链接列表表格' });
    expect(within(table).getAllByText('复核结果')).toHaveLength(2);
    expect(within(table).getByText('报告')).toBeInTheDocument();
  });

  it('filters share links by status and result type', async () => {
    const { user } = renderWithProviders(<AdminShareLinksPage />);

    expect(await screen.findByText('ABC123')).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText('链接状态'), 'revoked');
    expect(await screen.findByText('RPT456')).toBeInTheDocument();
    expect(screen.queryByText('ABC123')).not.toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText('内容类型'), 'review_result');
    const table = screen.getByRole('region', { name: '分享链接列表表格' });
    expect(await within(table).findByText('暂无符合条件的分享链接')).toBeInTheDocument();
  });
});
