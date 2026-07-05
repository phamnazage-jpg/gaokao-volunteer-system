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

  // ====== Data Query ======
  http.get(`${API}/data-query/score-line`, ({ request }) => {
    const url = new URL(request.url);
    const province = url.searchParams.get('province') ?? '广东';
    const year = Number(url.searchParams.get('year') ?? 2025);
    const scoreType = url.searchParams.get('scoreType') === 'history' ? 'history' : 'physics';

    return HttpResponse.json({
      province,
      year,
      scoreType,
      lines: [
        { batch: '本科批', score: scoreType === 'physics' ? 435 : 428, rank: scoreType === 'physics' ? 185000 : 65000 },
        { batch: '特殊类型招生控制线', score: scoreType === 'physics' ? 539 : 532, rank: scoreType === 'physics' ? 88000 : 24500 },
      ],
    });
  }),

  http.get(`${API}/data-query/rank-estimator`, ({ request }) => {
    const url = new URL(request.url);
    const province = url.searchParams.get('province') ?? '广东';
    const year = Number(url.searchParams.get('year') ?? 2025);
    const scoreType = url.searchParams.get('scoreType') === 'history' ? 'history' : 'physics';
    const rank = Number(url.searchParams.get('rank') ?? 12500);
    const baseScore = scoreType === 'physics' ? 621 : 603;
    const rankAdjustment = Math.max(-40, Math.min(30, Math.round((12500 - rank) / 1000)));

    return HttpResponse.json({
      province,
      year,
      scoreType,
      rank,
      equivalentScore: baseScore + rankAdjustment,
    });
  }),

  http.get(`${API}/data-query/majors`, ({ request }) => {
    const url = new URL(request.url);
    const keyword = (url.searchParams.get('keyword') ?? '').toLowerCase();
    const majors = [
      { id: 'major-cs', name: '计算机科学与技术', category: '工学' },
      { id: 'major-clinical', name: '临床医学', category: '医学' },
      { id: 'major-finance', name: '金融学', category: '经济学' },
    ].filter((item) => {
      if (!keyword) return true;
      return item.id.toLowerCase().includes(keyword) || item.name.toLowerCase().includes(keyword) || item.category.toLowerCase().includes(keyword);
    });

    return HttpResponse.json({
      majors,
      total: majors.length,
    });
  }),

  http.get(`${API}/data-query/schools`, ({ request }) => {
    const url = new URL(request.url);
    const keyword = (url.searchParams.get('keyword') ?? '').toLowerCase();
    const schools = [
      { id: 'school-sysu', name: '中山大学', province: '广东', is985: true, is211: true },
      { id: 'school-scut', name: '华南理工大学', province: '广东', is985: true, is211: true },
      { id: 'school-szu', name: '深圳大学', province: '广东', is985: false, is211: false },
      { id: 'school-zju', name: '浙江大学', province: '浙江', is985: true, is211: true },
    ].filter((item) => {
      if (!keyword) return true;
      const tags = [item.is985 ? '985' : '', item.is211 ? '211' : ''].filter(Boolean).join(' ');
      return (
        item.id.toLowerCase().includes(keyword) ||
        item.name.toLowerCase().includes(keyword) ||
        item.province.toLowerCase().includes(keyword) ||
        tags.includes(keyword)
      );
    });

    return HttpResponse.json({
      schools,
      total: schools.length,
    });
  }),

  // ====== Admin ======
  http.get(`${API}/admin/orders`, ({ request }) => {
    const url = new URL(request.url);
    const status = url.searchParams.get('status');
    const source = url.searchParams.get('source');
    const orders = [
      {
        id: 'GKO-2401',
        source: 'web',
        external_id: 'WEB-001',
        service_version: '2026-pro',
        status: 'paid',
        amount_cents: 129900,
        customer_name: '李家长',
        customer_phone: '13800138000',
        customer_wechat: 'li-parent',
        candidate_name: '李同学',
        candidate_province: '广东',
        assigned_consultant: '陈老师',
        intake_status: 'submitted',
        intake_submitted_at: '2026-07-03T09:00:00.000Z',
        created_at: '2026-07-03T08:30:00.000Z',
        status_updated_at: '2026-07-03T09:30:00.000Z',
        tags: ['重点跟进'],
      },
      {
        id: 'GKO-2402',
        source: 'wechat',
        external_id: 'WX-002',
        service_version: '2026-standard',
        status: 'serving',
        amount_cents: 99900,
        customer_name: '张家长',
        customer_phone: '13900139000',
        customer_wechat: 'zhang-parent',
        candidate_name: '张同学',
        candidate_province: '浙江',
        assigned_consultant: null,
        intake_status: 'draft',
        intake_submitted_at: null,
        created_at: '2026-07-02T10:00:00.000Z',
        status_updated_at: '2026-07-02T10:30:00.000Z',
        tags: [],
      },
    ].filter((order) => (!status || order.status === status) && (!source || order.source === source));

    return HttpResponse.json(orders);
  }),

  http.get(`${API}/admin/orders/:orderId`, ({ params }) => {
    const orderId = String(params['orderId'] ?? 'GKO-2401');
    return HttpResponse.json({
      order: {
        id: orderId,
        source: 'web',
        external_id: 'WEB-001',
        service_version: '2026-pro',
        status: 'serving',
        amount_cents: 129900,
        customer_name: '李家长',
        customer_phone: '13800138000',
        customer_wechat: 'li-parent',
        candidate_name: '李同学',
        candidate_province: '广东',
        candidate_score: 632,
        candidate_rank: 18234,
        candidate_subjects: ['物理', '化学', '生物'],
        assigned_consultant: '陈老师',
        intake_status: 'submitted',
        intake_submitted_at: '2026-07-03T09:00:00.000Z',
        created_at: '2026-07-03T08:30:00.000Z',
        status_updated_at: '2026-07-03T09:30:00.000Z',
        notes: '家长期望优先考虑计算机类和临床医学。',
        tags: ['重点跟进'],
      },
      history: [
        {
          id: 1,
          order_id: orderId,
          from_status: null,
          to_status: 'paid',
          actor: 'system',
          reason: '支付回调确认',
          changed_at: '2026-07-03T08:40:00.000Z',
        },
        {
          id: 2,
          order_id: orderId,
          from_status: 'paid',
          to_status: 'serving',
          actor: '陈老师',
          reason: '资料已提交，开始服务',
          changed_at: '2026-07-03T09:30:00.000Z',
        },
      ],
      available_next_statuses: ['delivered', 'completed', 'refunded'],
    });
  }),

  http.get(`${API}/admin/cases`, ({ request }) => {
    const url = new URL(request.url);
    const category = url.searchParams.get('category');
    const reviewStatus = url.searchParams.get('review_status');
    const items = [
      {
        id: 1,
        title: '低位次冲刺计算机成功案例',
        category: 'success',
        review_status: 'approved',
        review_note: '可作为官网展示案例。',
        reviewer: '运营主管',
        reviewed_at: '2026-07-03T12:00:00.000Z',
        summary: '通过院校梯度和专业组组合，帮助学生进入目标计算机方向。',
        content: '## 案例亮点\n\n- 目标明确\n- 梯度合理\n- 风险可控',
        tags: ['计算机', '广东', '冲稳保'],
        created_at: '2026-07-02T09:00:00.000Z',
        updated_at: '2026-07-03T12:00:00.000Z',
      },
      {
        id: 2,
        title: '医学方向风险提示案例',
        category: 'warning',
        review_status: 'pending',
        review_note: null,
        reviewer: null,
        reviewed_at: null,
        summary: '学生偏好集中在高热度医学专业，需要充分提示调剂和退档风险。',
        content: '## 风险点\n\n专业偏好过窄，需要补充保底方案。',
        tags: ['医学', '风险提示'],
        created_at: '2026-07-01T09:00:00.000Z',
        updated_at: '2026-07-01T10:00:00.000Z',
      },
    ].filter((item) => (!category || item.category === category) && (!reviewStatus || item.review_status === reviewStatus));

    return HttpResponse.json({
      total: items.length,
      limit: Number(url.searchParams.get('limit') ?? 50),
      offset: Number(url.searchParams.get('offset') ?? 0),
      items,
    });
  }),

  http.get(`${API}/admin/cases/:caseId`, ({ params }) => {
    const caseId = Number(params['caseId'] ?? 1);
    return HttpResponse.json({
      id: caseId,
      title: '低位次冲刺计算机成功案例',
      category: 'success',
      review_status: 'approved',
      review_note: '可作为官网展示案例。',
      reviewer: '运营主管',
      reviewed_at: '2026-07-03T12:00:00.000Z',
      summary: '通过院校梯度和专业组组合，帮助学生进入目标计算机方向。',
      content: '## 案例亮点\n\n- 目标明确\n- 梯度合理\n- 风险可控',
      tags: ['计算机', '广东', '冲稳保'],
      created_at: '2026-07-02T09:00:00.000Z',
      updated_at: '2026-07-03T12:00:00.000Z',
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

  http.get(`${API}/admin/share-links`, ({ request }) => {
    const url = new URL(request.url);
    const status = url.searchParams.get('status');
    const resultType = url.searchParams.get('result_type');
    const items = [
      {
        id: 'share-1',
        code: 'ABC123',
        share_url: 'https://example.test/s/ABC123',
        result_type: 'review_result',
        target_id: 'plan-001',
        created_at: '2026-07-01T08:00:00.000Z',
        expires_at_iso: '2026-08-01T08:00:00.000Z',
        revoked: false,
        access_count: 42,
        unique_visitors: 18,
        last_access_at_iso: '2026-07-04T08:30:00.000Z',
      },
      {
        id: 'share-2',
        code: 'RPT456',
        share_url: 'https://example.test/s/RPT456',
        result_type: 'report',
        target_id: 'report-2026-001',
        created_at: '2026-06-28T09:00:00.000Z',
        expires_at_iso: null,
        revoked: true,
        access_count: 9,
        unique_visitors: 3,
        last_access_at_iso: '2026-06-30T10:00:00.000Z',
      },
      {
        id: 'share-3',
        code: 'OLD789',
        share_url: 'https://example.test/s/OLD789',
        result_type: 'review_result',
        target_id: 'plan-expired',
        created_at: '2026-05-01T08:00:00.000Z',
        expires_at_iso: '2026-06-01T08:00:00.000Z',
        revoked: false,
        access_count: 2,
        unique_visitors: 1,
        last_access_at_iso: null,
      },
    ]
      .map((item) => ({
        ...item,
        status: item.revoked ? 'revoked' : item.expires_at_iso && new Date(item.expires_at_iso).getTime() <= Date.now() ? 'expired' : 'active',
      }))
      .filter((item) => (!status || item.status === status) && (!resultType || item.result_type === resultType));

    return HttpResponse.json({
      total: items.length,
      limit: Number(url.searchParams.get('limit') ?? 50),
      offset: Number(url.searchParams.get('offset') ?? 0),
      items,
    });
  }),

  http.get(`${API}/admin/share-links/:code`, ({ params }) => {
    const code = String(params['code'] ?? 'ABC123');
    const isReport = code === 'RPT456';
    const revoked = isReport;

    return HttpResponse.json({
      link: {
        id: `share-${code}`,
        code,
        share_url: `https://example.test/s/${code}`,
        result_type: isReport ? 'report' : 'review_result',
        target_id: isReport ? 'report-2026-001' : 'plan-001',
        created_at: '2026-07-01T08:00:00.000Z',
        expires_at_iso: isReport ? null : '2026-08-01T08:00:00.000Z',
        revoked,
        access_count: isReport ? 9 : 42,
        unique_visitors: isReport ? 3 : 18,
        last_access_at_iso: isReport ? '2026-06-30T10:00:00.000Z' : '2026-07-04T08:30:00.000Z',
      },
      stats: {
        access_count: isReport ? 9 : 42,
        unique_visitors: isReport ? 3 : 18,
        last_access_at_iso: isReport ? '2026-06-30T10:00:00.000Z' : '2026-07-04T08:30:00.000Z',
      },
      trend: [
        { date: '07/01', views: 6 },
        { date: '07/02', views: 10 },
        { date: '07/03', views: 12 },
        { date: '07/04', views: isReport ? 9 : 14 },
      ],
      audit_logs: [
        {
          id: 1,
          action: 'created',
          actor: 'system',
          created_at: '2026-07-01T08:00:00.000Z',
          note: 'Initial share link created',
        },
        {
          id: 2,
          action: revoked ? 'revoked' : 'viewed',
          actor: revoked ? 'operator' : 'visitor',
          created_at: revoked ? '2026-06-30T10:30:00.000Z' : '2026-07-04T08:30:00.000Z',
          note: revoked ? 'Manual revoke' : 'Latest access recorded',
        },
      ],
    });
  }),

  http.get(`${API}/admin/posters`, ({ request }) => {
    const url = new URL(request.url);
    const status = url.searchParams.get('status');
    const template = url.searchParams.get('template');
    const items = [
      {
        id: 'poster-job-1',
        jobId: 'poster-job-1',
        planId: 'plan-001',
        template: 'classic',
        status: 'completed',
        progress: 100,
        posterUrl: 'https://example.test/posters/poster-job-1.png',
        qrCode: 'https://example.test/qr/poster-job-1.png',
        createdAt: '2026-07-01T08:00:00.000Z',
        updatedAt: '2026-07-01T08:03:00.000Z',
        expiresAt: '2026-08-01T08:00:00.000Z',
      },
      {
        id: 'poster-job-2',
        jobId: 'poster-job-2',
        planId: 'plan-002',
        template: 'modern',
        status: 'processing',
        progress: 45,
        posterUrl: null,
        qrCode: null,
        createdAt: '2026-07-04T09:00:00.000Z',
        updatedAt: '2026-07-04T09:01:00.000Z',
        expiresAt: null,
      },
      {
        id: 'poster-job-3',
        jobId: 'poster-job-3',
        planId: 'plan-003',
        template: 'minimal',
        status: 'failed',
        progress: 100,
        posterUrl: null,
        qrCode: null,
        createdAt: '2026-07-03T09:00:00.000Z',
        updatedAt: '2026-07-03T09:02:00.000Z',
        expiresAt: null,
      },
    ].filter((item) => (!status || item.status === status) && (!template || item.template === template));

    return HttpResponse.json({
      total: items.length,
      limit: Number(url.searchParams.get('limit') ?? 50),
      offset: Number(url.searchParams.get('offset') ?? 0),
      items,
    });
  }),

  // ====== LLM ======
  http.get(`${API}/llm/config`, () => {
    return HttpResponse.json({
      currentProvider: 'claude',
      fallbackOrder: ['claude', 'gpt', 'gemini', 'deepseek'],
      availableProviders: ['claude', 'gpt', 'gemini', 'deepseek'],
    });
  }),
];
