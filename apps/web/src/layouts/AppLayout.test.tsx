import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
import { IntlProvider } from 'react-intl';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { messages } from '@/i18n/messages';
import { AppLayout } from './AppLayout';

function BrokenPage(): ReactNode {
  throw new Error('route render failed');
}

function renderAppLayoutWithBrokenRoute() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  vi.spyOn(console, 'error').mockImplementation(() => undefined);

  render(
    <QueryClientProvider client={queryClient}>
      <IntlProvider locale="zh-CN" messages={messages['zh-CN']} onError={() => undefined}>
        <MemoryRouter initialEntries={['/broken']}>
          <Routes>
            <Route path="/" element={<AppLayout />}>
              <Route index element={<main>首页已恢复</main>} />
              <Route path="broken" element={<BrokenPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      </IntlProvider>
    </QueryClientProvider>,
  );
}

describe('AppLayout error boundary', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders a fallback page for route crashes and recovers on navigation', async () => {
    expect(() => renderAppLayoutWithBrokenRoute()).not.toThrow();

    expect(screen.getByRole('heading', { name: '页面暂时无法显示' })).toBeInTheDocument();
    expect(screen.getByText('错误详情已隐藏，避免暴露内部信息。请重试或返回首页。')).toBeInTheDocument();
    expect(screen.queryByText('route render failed')).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('link', { name: '回到首页' }));

    expect(await screen.findByText('首页已恢复')).toBeInTheDocument();
  });
});
