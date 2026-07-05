import type { ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, within } from '@testing-library/react';
import { IntlProvider } from 'react-intl';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { AdminOrderDetailPage } from './OrderDetailPage';
import { messages } from '@/i18n/messages';

function renderOrderDetail(orderId = 'GKO-2401') {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <IntlProvider locale="zh-CN" messages={messages['zh-CN']} onError={() => undefined}>
          <MemoryRouter initialEntries={[`/admin/orders/${orderId}`]}>
            <Routes>
              <Route path="/admin/orders/:orderId" element={children} />
              <Route path="/admin/orders" element={<main>订单列表</main>} />
            </Routes>
          </MemoryRouter>
        </IntlProvider>
      </QueryClientProvider>
    );
  }

  return render(<AdminOrderDetailPage />, { wrapper: Wrapper });
}

describe('AdminOrderDetailPage', () => {
  it('loads order detail from generated admin order detail endpoint', async () => {
    renderOrderDetail();

    expect(screen.getByRole('status')).toHaveTextContent('正在加载订单详情');
    expect(await screen.findByRole('heading', { name: '订单详情 · GKO-2401' })).toBeInTheDocument();
    expect(screen.getByText('¥1,299.00')).toBeInTheDocument();
    expect(screen.getByText('李同学')).toBeInTheDocument();
    expect(screen.getByText('家长期望优先考虑计算机类和临床医学。')).toBeInTheDocument();
  });

  it('renders status history and available action buttons', async () => {
    renderOrderDetail();

    expect(await screen.findByRole('heading', { name: '订单详情 · GKO-2401' })).toBeInTheDocument();
    const history = screen.getByRole('region', { name: '订单状态历史' });

    expect(within(history).getByText('支付回调确认')).toBeInTheDocument();
    expect(within(history).getByText('资料已提交，开始服务')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '标记为已交付' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '标记为已完成' })).toBeInTheDocument();
  });
});
