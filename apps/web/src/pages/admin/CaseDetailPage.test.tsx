import type { ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { IntlProvider } from 'react-intl';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { AdminCaseDetailPage } from './CaseDetailPage';
import { messages } from '@/i18n/messages';

function renderCaseDetail(caseId = '1') {
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
          <MemoryRouter initialEntries={[`/admin/cases/${caseId}`]}>
            <Routes>
              <Route path="/admin/cases/:caseId" element={children} />
              <Route path="/admin/cases" element={<main>案例列表</main>} />
            </Routes>
          </MemoryRouter>
        </IntlProvider>
      </QueryClientProvider>
    );
  }

  return render(<AdminCaseDetailPage />, { wrapper: Wrapper });
}

describe('AdminCaseDetailPage', () => {
  it('loads case detail and renders markdown body', async () => {
    renderCaseDetail();

    expect(screen.getByRole('status')).toHaveTextContent('正在加载案例详情');
    expect(await screen.findByRole('heading', { name: '低位次冲刺计算机成功案例' })).toBeInTheDocument();
    expect(screen.getByText('可作为官网展示案例。')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: '案例亮点' })).toBeInTheDocument();
    expect(screen.getByText('梯度合理')).toBeInTheDocument();
  });

  it('rejects invalid case ids before querying', () => {
    renderCaseDetail('abc');

    expect(screen.getByRole('alert')).toHaveTextContent('案例 ID 无效');
  });
});
