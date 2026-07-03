import { z } from 'zod';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { apiClient, HttpError } from './api-client';

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
});
