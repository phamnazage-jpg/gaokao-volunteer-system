import { describe, expect, it } from 'vitest';
import { IntlProvider } from 'react-intl';
import { screen } from '@testing-library/react';
import { AdminDashboardPage } from './DashboardPage';
import { renderWithProviders } from '@/test/renderWithProviders';
import { messages } from '@/i18n/messages';

function renderDashboard() {
  return renderWithProviders(
    <IntlProvider locale="zh-CN" messages={messages['zh-CN']} onError={() => undefined}>
      <AdminDashboardPage />
    </IntlProvider>,
  );
}

describe('AdminDashboardPage', () => {
  it('renders Sprint 7 admin dashboard metrics and recent orders', () => {
    renderDashboard();

    expect(screen.getByRole('heading', { name: '运营概览' })).toBeInTheDocument();
    expect(screen.getByRole('region', { name: '运营统计' })).toHaveTextContent('总订单');
    expect(screen.getByRole('img', { name: '最近 7 天订单趋势折线图' })).toBeInTheDocument();
    expect(screen.getByText('GKO-2401')).toBeInTheDocument();
  });
});
