import { describe, expect, it } from 'vitest';
import { IntlProvider } from 'react-intl';
import { screen } from '@testing-library/react';
import { AdminErrorPage } from './ErrorPage';
import { renderWithProviders } from '@/test/renderWithProviders';
import { messages } from '@/i18n/messages';

function renderAdminErrorPage() {
  return renderWithProviders(
    <IntlProvider locale="zh-CN" messages={messages['zh-CN']} onError={() => undefined}>
      <AdminErrorPage />
    </IntlProvider>,
  );
}

describe('AdminErrorPage', () => {
  it('renders an actionable admin error fallback', () => {
    renderAdminErrorPage();

    expect(screen.getByRole('heading', { name: '后台页面暂时无法显示' })).toBeInTheDocument();
    expect(screen.getByText('返回概览确认系统状态')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '刷新重试' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '返回运营概览' })).toHaveAttribute('href', '/admin');
  });
});
