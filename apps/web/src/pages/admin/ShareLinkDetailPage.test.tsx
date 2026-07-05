import { describe, expect, it } from 'vitest';
import { render } from '@testing-library/react';
import { screen, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { IntlProvider } from 'react-intl';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AdminShareLinkDetailPage } from './ShareLinkDetailPage';
import { messages } from '@/i18n/messages';

function renderDetailPage(code = 'ABC123') {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <IntlProvider locale="zh-CN" messages={messages['zh-CN']} onError={() => undefined}>
        <MemoryRouter initialEntries={[`/admin/share-links/${code}`]}>
          <Routes>
            <Route path="/admin/share-links/:code" element={<AdminShareLinkDetailPage />} />
          </Routes>
        </MemoryRouter>
      </IntlProvider>
    </QueryClientProvider>,
  );
}

describe('AdminShareLinkDetailPage', () => {
  it('loads share link basic info, stats, trend and audit logs', async () => {
    renderDetailPage();

    expect(screen.getByRole('status')).toHaveTextContent('正在加载分享链接详情');
    expect(await screen.findByRole('heading', { name: '分享链接详情 · ABC123' })).toBeInTheDocument();
    expect(screen.getByText('example.test/s/ABC123')).toBeInTheDocument();
    expect(screen.getByText('plan-001')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('18')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: '访问趋势' })).toBeInTheDocument();

    const audit = screen.getByRole('region', { name: '分享链接操作日志' });
    expect(within(audit).getByText('created')).toBeInTheDocument();
    expect(within(audit).getByText('viewed')).toBeInTheDocument();
  });

  it('renders revoked report share link details', async () => {
    renderDetailPage('RPT456');

    expect(await screen.findByRole('heading', { name: '分享链接详情 · RPT456' })).toBeInTheDocument();
    expect(screen.getByText('报告 / 已撤销 / example.test/s/RPT456')).toBeInTheDocument();
    expect(screen.getByText('report-2026-001')).toBeInTheDocument();
    expect(screen.getByText('Manual revoke')).toBeInTheDocument();
  });
});
