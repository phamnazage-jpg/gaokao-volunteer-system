import { describe, expect, it } from 'vitest';
import { IntlProvider } from 'react-intl';
import { screen, within } from '@testing-library/react';
import { AdminOrdersPage } from './OrdersPage';
import { renderWithProviders } from '@/test/renderWithProviders';
import { messages } from '@/i18n/messages';

function renderOrdersPage() {
  return renderWithProviders(
    <IntlProvider locale="zh-CN" messages={messages['zh-CN']} onError={() => undefined}>
      <AdminOrdersPage />
    </IntlProvider>,
  );
}

describe('AdminOrdersPage', () => {
  it('loads admin orders from the generated admin orders endpoint', async () => {
    renderOrdersPage();

    expect(screen.getByRole('status')).toHaveTextContent('正在加载订单');
    expect(await screen.findByText('GKO-2401')).toBeInTheDocument();
    expect(screen.getByText('李同学')).toBeInTheDocument();
    expect(screen.getByText('¥1,299.00')).toBeInTheDocument();
    expect(screen.getByText('GKO-2402')).toBeInTheDocument();
  });

  it('filters orders by status and source', async () => {
    const { user } = renderOrdersPage();

    expect(await screen.findByText('GKO-2401')).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText('订单状态'), 'paid');
    expect(await screen.findByText('GKO-2401')).toBeInTheDocument();
    expect(screen.queryByText('GKO-2402')).not.toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText('订单来源'), 'wechat');
    const tableRegion = screen.getByRole('region', { name: '订单列表表格' });
    expect(await within(tableRegion).findByText('暂无符合条件的订单')).toBeInTheDocument();
  });
});
