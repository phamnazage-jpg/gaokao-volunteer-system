/**
 * V10 选项 B · MSW handlers (5 模块端点)
 * Sprint 2 提供基础 handlers, 真实后端联通在 Sprint 3 完成
 */
import { http, HttpResponse } from 'msw';

const API = '/api';

export const handlers = [
  // ====== Chat ======
  http.post(`${API}/chat/send`, () => {
    return HttpResponse.json({
      sessionId: '00000000-0000-0000-0000-000000000001',
      userMessageId: 'user-1',
      assistantMessageId: 'assistant-1',
      assistantMessage: {
        id: 'assistant-1',
        role: 'assistant',
        content: 'Mock reply: 收到您的消息',
        timestamp: new Date().toISOString(),
      },
    });
  }),

  http.get(`${API}/chat/history`, ({ request }) => {
    const url = new URL(request.url);
    const sessionId = url.searchParams.get('sessionId') ?? 'default';
    return HttpResponse.json({
      sessionId,
      messages: [
        {
          id: 'welcome',
          role: 'assistant',
          content: '👋 你好！',
          timestamp: new Date().toISOString(),
        },
      ],
    });
  }),

  // ====== Consultations ======
  http.get(`${API}/consultations`, () => {
    return HttpResponse.json({
      consultations: [
        {
          id: 'c1',
          title: '广东物理 620 咨询',
          messageCount: 12,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      ],
      total: 1,
    });
  }),

  // ====== Plans ======
  http.get(`${API}/plans`, () => {
    return HttpResponse.json({
      plans: [
        {
          id: 'p1',
          name: '冲稳保方案 #1',
          rush: [],
          stable: [],
          safe: [],
          createdAt: new Date().toISOString(),
        },
      ],
      total: 1,
    });
  }),

  // ====== Share Link ======
  http.post(`${API}/share-link`, async ({ request }) => {
    const payload = (await request.json()) as { target_token?: string; ttl_days?: number };
    return HttpResponse.json(
      {
        code: 'ABC123',
        share_url: 'https://example.test/s/ABC123',
        target_id: payload.target_token ?? 'plan-001',
        result_type: 'review_result',
        expires_at_iso: payload.ttl_days ? new Date(Date.now() + payload.ttl_days * 86_400_000).toISOString() : null,
        revoked: false,
      },
      { status: 201 },
    );
  }),

  http.get(`${API}/share-link/latest`, () => {
    return HttpResponse.json({
      code: 'ABC123',
      share_url: 'https://example.test/s/ABC123',
      target_id: 'plan-001',
      result_type: 'review_result',
      expires_at_iso: null,
      revoked: false,
    });
  }),

  http.post(`${API}/share-link/:code/revoke`, ({ params }) => {
    return HttpResponse.json({
      code: params['code'],
      revoked: true,
      changed: true,
    });
  }),

  http.get(`${API}/share-link/:code/stats`, () => {
    return HttpResponse.json({
      views: 12,
      uniqueVisitors: 5,
      lastAccessedAt: '2026-07-03T00:00:00.000Z',
    });
  }),
];
