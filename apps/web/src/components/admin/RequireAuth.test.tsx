import { describe, expect, it, vi } from 'vitest';
import { render } from '@testing-library/react';
import { screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { IntlProvider } from 'react-intl';
import { RequireAuth } from './RequireAuth';
import { messages } from '@/i18n/messages';
import { useUserStore } from '@/stores/user';

function renderGuard(initialPath = '/admin') {
  return render(
    <IntlProvider locale="zh-CN" messages={messages['zh-CN']} onError={() => undefined}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route
            path="/admin"
            element={
              <RequireAuth>
                <main>后台内容</main>
              </RequireAuth>
            }
          />
          <Route path="/admin/login" element={<main>登录页</main>} />
          <Route path="/403" element={<main>权限不足</main>} />
        </Routes>
      </MemoryRouter>
    </IntlProvider>,
  );
}

interface AdminSessionOverrides {
  tokenExpiresAt?: number;
  role?: 'user' | 'admin';
}

function seedAdminSession(overrides: AdminSessionOverrides = {}): void {
  useUserStore.getState().setAdminSession({
    username: 'admin',
    accessToken: 'jwt-token',
    tokenType: 'bearer',
    expiresIn: 3600,
  });
  if (overrides.tokenExpiresAt !== undefined) {
    useUserStore.setState({ tokenExpiresAt: overrides.tokenExpiresAt });
  }
  if (overrides.role !== undefined) {
    useUserStore.setState({ role: overrides.role });
  }
}

describe('RequireAuth', () => {
  it('redirects anonymous users to admin login', async () => {
    renderGuard();

    expect(await screen.findByText('登录页')).toBeInTheDocument();
  });

  it('redirects users without an active token to admin login', async () => {
    useUserStore.getState().setUser({
      id: 'admin-1',
      name: '管理员',
      phone: '13800138000',
      role: 'admin',
    });

    renderGuard();

    expect(await screen.findByText('登录页')).toBeInTheDocument();
  });

  it('redirects expired admin sessions to admin login and clears auth state', async () => {
    seedAdminSession({ tokenExpiresAt: Date.now() - 1000 });

    renderGuard();

    expect(await screen.findByText('登录页')).toBeInTheDocument();
    expect(useUserStore.getState()).toMatchObject({ isLoggedIn: false, token: null });
  });

  it('redirects non-admin users to forbidden page after backend verification', async () => {
    seedAdminSession({ role: 'user' });
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ id: 1, username: 'viewer', role: 'viewer', is_active: true, created_at: '2026-07-05T00:00:00+00:00' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );

    renderGuard();

    expect(await screen.findByText('权限不足')).toBeInTheDocument();
  });

  it('verifies the token with /api/auth/me before rendering children for admin users', async () => {
    seedAdminSession();
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: 1, username: 'admin', role: 'admin', is_active: true, created_at: '2026-07-05T00:00:00+00:00' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    renderGuard();

    expect(await screen.findByText('后台内容')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledOnce();
    const calls = fetchMock.mock.calls as Array<[string, RequestInit]>;
    expect(calls[0][0]).toBe('/api/auth/me');
    expect(calls[0][1].method).toBe('GET');
    const headers = calls[0][1].headers as Record<string, string>;
    expect(headers.Authorization).toBe('Bearer jwt-token');
  });

  it('logs out and redirects to login when backend verification rejects the token', async () => {
    seedAdminSession();
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ code: 'E01202', message: 'invalid token' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );

    renderGuard();

    expect(await screen.findByText('登录页')).toBeInTheDocument();
    expect(useUserStore.getState()).toMatchObject({ isLoggedIn: false, token: null });
  });
});
