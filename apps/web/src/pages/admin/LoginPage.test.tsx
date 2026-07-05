import { describe, expect, it } from 'vitest';
import { render } from '@testing-library/react';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { IntlProvider } from 'react-intl';
import { AdminLoginPage } from './LoginPage';
import { messages } from '@/i18n/messages';
import { useUserStore } from '@/stores/user';

function renderLogin() {
  const user = userEvent.setup();
  const view = render(
    <IntlProvider locale="zh-CN" messages={messages['zh-CN']} onError={() => undefined}>
      <MemoryRouter initialEntries={['/admin/login']}>
        <Routes>
          <Route path="/admin/login" element={<AdminLoginPage />} />
          <Route path="/admin" element={<main>后台首页</main>} />
        </Routes>
      </MemoryRouter>
    </IntlProvider>,
  );

  return { user, ...view };
}

describe('AdminLoginPage', () => {
  it('validates phone and code fields', async () => {
    const { user } = renderLogin();

    await user.click(screen.getByRole('button', { name: '登录后台' }));

    expect(await screen.findByText('请输入 11 位管理员手机号')).toBeInTheDocument();
    expect(screen.getByText('请输入 6 位验证码')).toBeInTheDocument();
  });

  it('shows mock code error when code is not accepted', async () => {
    const { user } = renderLogin();

    await user.type(screen.getByLabelText('手机号'), '13800138000');
    await user.type(screen.getByLabelText('验证码'), '654321');
    await user.click(screen.getByRole('button', { name: '登录后台' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('验证码错误');
    expect(useUserStore.getState().isLoggedIn).toBe(false);
  });

  it('logs in with local mock code and redirects to dashboard', async () => {
    const { user } = renderLogin();

    await user.type(screen.getByLabelText('手机号'), '13800138000');
    await user.type(screen.getByLabelText('验证码'), '123456');
    await user.click(screen.getByRole('button', { name: '登录后台' }));

    expect(await screen.findByText('后台首页')).toBeInTheDocument();
    expect(useUserStore.getState()).toMatchObject({
      isLoggedIn: true,
      role: 'admin',
      phone: '13800138000',
    });
  });
});
