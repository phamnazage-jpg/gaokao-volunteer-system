import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { IntlProvider } from 'react-intl';
import { screen } from '@testing-library/react';
import { AdminDashboardPage } from './DashboardPage';
import { renderWithProviders } from '@/test/renderWithProviders';
import { server } from '@/test/mocks/server';
import { messages } from '@/i18n/messages';

function renderDashboard(locale: 'zh-CN' | 'en-US' = 'zh-CN') {
  return renderWithProviders(
    <IntlProvider locale={locale} messages={messages[locale]} onError={() => undefined}>
      <AdminDashboardPage />
    </IntlProvider>,
  );
}

describe('AdminDashboardPage', () => {
  it('renders Sprint 7 admin dashboard metrics and recent orders', async () => {
    renderDashboard();

    expect(screen.getByRole('heading', { name: '运营概览' })).toBeInTheDocument();
    expect(screen.getByRole('region', { name: '运营统计' })).toHaveTextContent('总订单');
    expect(screen.getByRole('img', { name: '最近 7 天订单趋势折线图' })).toBeInTheDocument();
    expect(await screen.findByText('GKO-2401')).toBeInTheDocument();
  });

  it('renders KPI values from the admin dashboard stats API', async () => {
    server.use(
      http.get('/api/admin/stats/dashboard', () =>
        HttpResponse.json({
          summary: {
            total_orders: 7,
            pending_orders: 2,
            total_users: 3,
            total_shares: 4,
          },
          by_status: {},
          by_source: {},
          by_service_version: {},
          trends: {
            orders_7d: [
              { date: '2026-07-06', count: 5 },
              { date: '2026-07-07', count: 6 },
            ],
          },
          generated_at: '2026-07-07T00:00:00.000Z',
        }),
      ),
    );

    renderDashboard();

    const metrics = screen.getByRole('region', { name: '运营统计' });
    expect(await screen.findByText('GKO-2401')).toBeInTheDocument();
    expect(metrics).toHaveTextContent('总订单');
    expect(metrics).toHaveTextContent('7');
    expect(metrics).toHaveTextContent('待审核');
    expect(metrics).toHaveTextContent('2');
    expect(metrics).toHaveTextContent('总用户');
    expect(metrics).toHaveTextContent('3');
    expect(metrics).toHaveTextContent('总分享');
    expect(metrics).toHaveTextContent('4');
    expect(metrics).not.toHaveTextContent('1,248');
    expect(metrics).not.toHaveTextContent('8,902');
    expect(metrics).not.toHaveTextContent('2,416');
  });

  it.each([
    ['zh-CN', /Mock 数据|待接真实 API/],
    ['en-US', /Mock data|awaiting real API/i],
  ] as const)('does not display mock API placeholder copy in %s', (locale, placeholderCopy) => {
    renderDashboard(locale);

    expect(screen.queryByText(placeholderCopy)).not.toBeInTheDocument();
  });
});
