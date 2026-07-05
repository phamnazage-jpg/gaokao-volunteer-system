import { describe, expect, it } from 'vitest';
import { render } from '@testing-library/react';
import { screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { RequireAuth } from './RequireAuth';
import { useUserStore } from '@/stores/user';

function renderGuard(initialPath = '/admin') {
  return render(
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
    </MemoryRouter>,
  );
}

describe('RequireAuth', () => {
  it('redirects anonymous users to admin login', async () => {
    renderGuard();

    expect(await screen.findByText('登录页')).toBeInTheDocument();
  });

  it('redirects non-admin users to forbidden page', async () => {
    useUserStore.getState().setUser({
      id: 'user-1',
      name: '普通用户',
      phone: '13800138000',
      role: 'user',
    });

    renderGuard();

    expect(await screen.findByText('权限不足')).toBeInTheDocument();
  });

  it('renders children for admin users', () => {
    useUserStore.getState().setUser({
      id: 'admin-1',
      name: '管理员',
      phone: '13800138000',
      role: 'admin',
    });

    renderGuard();

    expect(screen.getByText('后台内容')).toBeInTheDocument();
  });
});
