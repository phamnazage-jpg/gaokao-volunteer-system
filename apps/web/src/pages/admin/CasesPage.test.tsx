import { describe, expect, it } from 'vitest';
import { IntlProvider } from 'react-intl';
import { screen, within } from '@testing-library/react';
import { AdminCasesPage } from './CasesPage';
import { renderWithProviders } from '@/test/renderWithProviders';
import { messages } from '@/i18n/messages';

function renderCasesPage() {
  return renderWithProviders(
    <IntlProvider locale="zh-CN" messages={messages['zh-CN']} onError={() => undefined}>
      <AdminCasesPage />
    </IntlProvider>,
  );
}

describe('AdminCasesPage', () => {
  it('loads admin cases from generated admin cases endpoint', async () => {
    renderCasesPage();

    expect(screen.getByRole('status')).toHaveTextContent('正在加载案例');
    expect(await screen.findByText('低位次冲刺计算机成功案例')).toBeInTheDocument();
    expect(screen.getByText('医学方向风险提示案例')).toBeInTheDocument();
    const grid = screen.getByRole('region', { name: '案例列表网格' });
    expect(within(grid).getByText('成功案例')).toBeInTheDocument();
    expect(within(grid).getByText('风险案例')).toBeInTheDocument();
  });

  it('filters cases by category and review status', async () => {
    const { user } = renderCasesPage();

    expect(await screen.findByText('低位次冲刺计算机成功案例')).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText('案例类型'), 'warning');
    expect(await screen.findByText('医学方向风险提示案例')).toBeInTheDocument();
    expect(screen.queryByText('低位次冲刺计算机成功案例')).not.toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText('审核状态'), 'approved');
    const grid = screen.getByRole('region', { name: '案例列表网格' });
    expect(await within(grid).findByText('暂无符合条件的案例')).toBeInTheDocument();
  });
});
