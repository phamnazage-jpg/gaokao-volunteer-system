import { afterEach, describe, expect, it, vi } from 'vitest';
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
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('validates username and password fields', async () => {
    const { user } = renderLogin();

    await user.click(screen.getByRole('button', { name: '登录后台' }));

    expect(await screen.findByText('请输入管理员用户名')).toBeInTheDocument();
    expect(screen.getByText('请输入管理员密码')).toBeInTheDocument();
  });

  it('shows backend login error when credentials are rejected', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ code: 'E01101', message: 'bad credentials' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );
    const { user } = renderLogin();

    await user.type(screen.getByLabelText('用户名'), 'admin');
    await user.type(screen.getByLabelText('密码'), 'wrong-password');
    await user.click(screen.getByRole('button', { name: '登录后台' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('用户名或密码不正确');
    expect(useUserStore.getState().isLoggedIn).toBe(false);
  });

  it('logs in through /api/auth/login and stores token metadata', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ access_token: 'jwt-token', token_type: 'bearer', expires_in: 3600 }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);
    const { user } = renderLogin();

    await user.type(screen.getByLabelText('用户名'), 'admin');
    await user.type(screen.getByLabelText('密码'), 'StrongPass1!');
    await user.click(screen.getByRole('button', { name: '登录后台' }));

    expect(await screen.findByText('后台首页')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/auth/login',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ username: 'admin', password: 'StrongPass1!' }),
      }),
    );
    expect(useUserStore.getState()).toMatchObject({
      isLoggedIn: true,
      role: 'admin',
      token: 'jwt-token',
      tokenType: 'bearer',
    });
    expect(useUserStore.getState().tokenExpiresAt).toBeGreaterThan(Date.now());
  });
});
