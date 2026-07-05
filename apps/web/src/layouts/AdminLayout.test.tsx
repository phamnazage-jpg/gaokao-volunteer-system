import { describe, expect, it, vi } from 'vitest';
import type { ReactElement } from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AdminLayout } from './AdminLayout';
import { messages } from '@/i18n/messages';
import { useUserStore } from '@/stores/user';

function BrokenAdminChild(): ReactElement {
  throw new Error('admin child exploded');
}

function renderAdminLayoutWithBrokenChild() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  useUserStore.getState().setUser({
    id: 'admin-1',
    name: 'Admin',
    phone: '13800138000',
    role: 'admin',
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <IntlProvider locale="zh-CN" messages={messages['zh-CN']} onError={() => undefined}>
        <MemoryRouter initialEntries={['/admin/orders']}>
          <Routes>
            <Route path="/admin" element={<AdminLayout />}>
              <Route path="orders" element={<BrokenAdminChild />} />
            </Route>
          </Routes>
        </MemoryRouter>
      </IntlProvider>
    </QueryClientProvider>,
  );
}

describe('AdminLayout', () => {
  it('uses the admin error page when an admin child route crashes', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => undefined);

    try {
      renderAdminLayoutWithBrokenChild();

      expect(await screen.findByRole('heading', { name: '后台页面暂时无法显示' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: '返回运营概览' })).toHaveAttribute('href', '/admin');

      await userEvent.click(screen.getByRole('button', { name: '刷新重试' }));

      expect(await screen.findByRole('heading', { name: '后台页面暂时无法显示' })).toBeInTheDocument();
    } finally {
      consoleError.mockRestore();
    }
  });
});
