import { z } from 'zod';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useUserStore } from '@/stores/user';
import { apiClient, HttpError } from './api-client';

function setNavigatorOnline(value: boolean): void {
  Object.defineProperty(window.navigator, 'onLine', {
    configurable: true,
    value,
  });
}

const errorCases = [
  ['E01101', '用户名或密码不正确'],
  ['E01102', '账号已被停用'],
  ['E01201', '登录状态已过期'],
  ['E01202', '登录凭证无效'],
  ['E01301', '当前账号无访问权限'],
  ['E02001', '未找到该订单'],
  ['E02002', '订单仍在数据保留期内'],
  ['E02301', '订单当前状态不支持该操作'],
  ['E02501', '请求过于频繁'],
  ['E03001', '请求数据未通过校验'],
  ['E03002', '未找到对应的数据'],
  ['E03003', '数据保存失败'],
  ['E04001', '外部服务暂时不可用'],
  ['E04002', '外部服务响应超时'],
  ['E05001', '系统内部异常'],
  ['E05002', '系统配置缺失'],
  ['E05003', '系统资源不足'],
] as const;

describe('apiClient error handling', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    setNavigatorOnline(true);
  });

  it.each(errorCases)('maps backend error code %s to localized user copy', async (code, message) => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            code,
            message: `backend raw message for ${code}`,
            details: { requestId: 'req-1' },
          }),
          {
            status: 422,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      ),
    );

    await expect(apiClient.get('/boom', z.object({ ok: z.boolean() }))).rejects.toMatchObject({
      name: 'HttpError',
      status: 422,
      code,
      message,
      details: { requestId: 'req-1' },
    });
  });

  it('falls back to the backend message for unknown error codes', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ code: 'E09999', message: 'backend fallback', details: null }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );

    await expect(apiClient.get('/unknown', z.object({ ok: z.boolean() }))).rejects.toMatchObject({
      name: 'HttpError',
      status: 500,
      code: 'E09999',
      message: 'backend fallback',
      details: null,
    } satisfies Partial<HttpError>);
  });

  it('queues non-GET requests while offline and resumes them when online', async () => {
    setNavigatorOnline(false);
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    const request = apiClient.post('/queued-write', { value: 1 }, z.object({ ok: z.boolean() }));
    await Promise.resolve();

    expect(fetchMock).not.toHaveBeenCalled();

    setNavigatorOnline(true);
    window.dispatchEvent(new Event('online'));

    await expect(request).resolves.toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledWith('/api/queued-write', expect.objectContaining({ method: 'POST' }));
  });

  it('injects Authorization Bearer from the admin session token', async () => {
    useUserStore.getState().setAdminSession({
      username: 'admin',
      accessToken: 'jwt-token',
      tokenType: 'bearer',
      expiresIn: 3600,
    });
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    await expect(apiClient.get('/admin/orders', z.object({ ok: z.boolean() }))).resolves.toEqual({ ok: true });

    expect(fetchMock).toHaveBeenCalledOnce();
    const calls = fetchMock.mock.calls as Array<[string, RequestInit]>;
    expect(calls[0][0]).toBe('/api/admin/orders');
    const headers = calls[0][1].headers as Record<string, string>;
    expect(headers.Authorization).toBe('Bearer jwt-token');
  });

  it('does not inject Authorization after the admin token has expired', async () => {
    useUserStore.getState().setAdminSession({
      username: 'admin',
      accessToken: 'expired-token',
      tokenType: 'bearer',
      expiresIn: -1,
    });
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    await expect(apiClient.get('/admin/orders', z.object({ ok: z.boolean() }))).resolves.toEqual({ ok: true });

    expect(fetchMock).toHaveBeenCalledOnce();
    const calls = fetchMock.mock.calls as Array<[string, RequestInit]>;
    expect(calls[0][0]).toBe('/api/admin/orders');
    const headers = calls[0][1].headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
  });
});
