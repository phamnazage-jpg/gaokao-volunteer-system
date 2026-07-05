import { expect, test, type Page } from '@playwright/test';

async function seedAdminSession(page: Page): Promise<void> {
  await page.addInitScript(() => {
    window.localStorage.setItem(
      'gaokao-user-store',
      JSON.stringify({
        state: {
          id: 'admin:e2e-admin',
          name: 'e2e-admin',
          phone: null,
          role: 'admin',
          isLoggedIn: true,
          token: 'e2e-jwt-token',
          tokenType: 'bearer',
          tokenExpiresAt: Date.now() + 60 * 60 * 1000,
        },
        version: 0,
      }),
    );
  });
}

async function mockAdminApi(page: Page): Promise<void> {
  await page.route('**/api/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 1,
        username: 'e2e-admin',
        role: 'admin',
        is_active: true,
        created_at: '2026-07-05T00:00:00.000Z',
      }),
    });
  });

  await page.route('**/api/admin/orders**', async (route) => {
    if (route.request().url().includes('/api/admin/orders/GKO-2401')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          order: {
            id: 'GKO-2401',
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
              order_id: 'GKO-2401',
              from_status: null,
              to_status: 'paid',
              actor: 'system',
              reason: '支付回调确认',
              changed_at: '2026-07-03T08:40:00.000Z',
            },
          ],
          available_next_statuses: ['delivered', 'completed', 'refunded'],
        }),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
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
      ]),
    });
  });

  await page.route('**/api/admin/cases**', async (route) => {
    if (route.request().url().includes('/api/admin/cases/1')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
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
        }),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: 1,
        limit: 12,
        offset: 0,
        items: [
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
        ],
      }),
    });
  });
}

test.describe('Admin portal (Sprint 7)', () => {
  test('anonymous users are redirected to login and can enter the admin dashboard', async ({ page }) => {
    await mockAdminApi(page);
    await page.route('**/api/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ access_token: 'e2e-jwt-token', token_type: 'bearer', expires_in: 3600 }),
      });
    });
    await page.goto('/admin');

    await expect(page).toHaveURL(/\/admin\/login/);
    await page.getByLabel('用户名').fill('admin');
    await page.getByLabel('密码').fill('StrongPass1!');
    await page.getByRole('button', { name: '登录后台' }).click();

    await expect(page).toHaveURL(/\/admin$/);
    await expect(page.getByRole('heading', { name: '运营概览' })).toBeVisible();
  });

  test('admin users can navigate orders and cases from the protected layout', async ({ page }) => {
    await seedAdminSession(page);
    await mockAdminApi(page);

    await page.goto('/admin');
    await expect(page.getByRole('navigation', { name: '后台导航' })).toBeVisible();

    await page.getByRole('link', { name: '订单' }).click();
    await expect(page).toHaveURL(/\/admin\/orders$/);
    await expect(page.getByRole('heading', { name: '订单列表' })).toBeVisible();
    await expect(page.getByText('GKO-2401')).toBeVisible();

    await page.goto('/admin/orders/GKO-2401');
    await expect(page.getByRole('heading', { name: /GKO-2401/ })).toBeVisible();
    await expect(page.getByText('支付回调确认')).toBeVisible();

    await page.getByRole('link', { name: '案例' }).click();
    await expect(page).toHaveURL(/\/admin\/cases$/);
    await expect(page.getByRole('heading', { name: '案例列表' })).toBeVisible();
    await expect(page.getByText('低位次冲刺计算机成功案例')).toBeVisible();

    await page.goto('/admin/cases/1');
    await expect(page.getByRole('heading', { name: '低位次冲刺计算机成功案例' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '案例亮点' })).toBeVisible();
  });

  test('all admin navigation links resolve to concrete routes', async ({ page }) => {
    await seedAdminSession(page);
    await mockAdminApi(page);
    await page.route('**/api/**', async (route) => {
      const url = route.request().url();
      if (url.includes('/api/auth/me')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            username: 'e2e-admin',
            role: 'admin',
            is_active: true,
            created_at: '2026-07-05T00:00:00.000Z',
          }),
        });
        return;
      }
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], total: 0, limit: 12, offset: 0 }) });
    });

    const navTargets = [
      { label: '概览', pattern: /\/admin$/ },
      { label: '订单', pattern: /\/admin\/orders$/ },
      { label: '案例', pattern: /\/admin\/cases$/ },
      { label: '分享链接', pattern: /\/admin\/share-links$/ },
      { label: '分数线', pattern: /\/admin\/score-lines$/ },
      { label: '位次估算', pattern: /\/admin\/rank-estimator$/ },
      { label: '专业库', pattern: /\/admin\/majors$/ },
      { label: '院校库', pattern: /\/admin\/schools$/ },
      { label: '复核', pattern: /\/admin\/review$/ },
      { label: '海报', pattern: /\/admin\/posters$/ },
    ];

    await page.goto('/admin');
    for (const target of navTargets) {
      await page.getByRole('link', { name: target.label }).first().click();
      await expect(page).toHaveURL(target.pattern);
      await expect(page.getByRole('heading', { name: '页面不存在' })).toHaveCount(0);
    }
  });

  test('admin error fallback provides recovery actions', async ({ page }) => {
    await seedAdminSession(page);
    await mockAdminApi(page);

    await page.goto('/admin/error');

    await expect(page.getByRole('heading', { name: '后台页面暂时无法显示' })).toBeVisible();
    await expect(page.getByRole('button', { name: '刷新重试' })).toBeVisible();
    await expect(page.getByRole('link', { name: '返回运营概览' })).toHaveAttribute('href', '/admin');
  });
});
