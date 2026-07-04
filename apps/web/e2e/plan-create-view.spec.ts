/**
 * V10 · Sprint 4 · T-B-23.4 · e2e: plans list + detail (真实存在的 UI)
 *
 * PlanSchema: { id, name, rush: [{ university, major, estScore, probability, risk, riskType, reason }],
 *                stable: [], safe: [], createdAt }
 * PlanDetailPage 实际是 section 形式（冲刺/稳妥/保底），而不是 3-Tab
 */
import { test, expect } from '@playwright/test';

test.describe('Plans List + Detail (V10 Sprint 4 · T-B-23.4)', () => {
  test('plans list page renders empty state', async ({ page }) => {
    await page.route('**/api/plans**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ plans: [], total: 0 }),
      });
    });

    await page.goto('/plans');
    await expect(page.getByRole('heading', { name: '我的方案' })).toBeVisible();
    await expect(page.getByText('暂无方案')).toBeVisible();
  });

  test('plans list page renders a plan and links to detail', async ({ page }) => {
    await page.route('**/api/plans**', async (route) => {
      const url = route.request().url();
      if (url.endsWith('/api/plans') || url.includes('/api/plans?')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            plans: [
              {
                id: 'plan-e2e-1',
                name: '广东物理 620 冲刺方案',
                rush: [],
                stable: [],
                safe: [],
                createdAt: '2026-07-01T10:00:00Z',
              },
            ],
            total: 1,
          }),
        });
      } else {
        await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
      }
    });

    await page.goto('/plans');
    await expect(page.getByText('广东物理 620 冲刺方案')).toBeVisible();

    const link = page.locator('a[href="/plans/plan-e2e-1"]');
    await expect(link).toBeVisible();
  });

  test('plan detail page renders rush/stable/safe sections', async ({ page }) => {
    const planId = 'plan-e2e-detail';

    await page.route('**/api/plans/' + planId, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: planId,
          name: '广东物理 620 冲刺方案',
          rush: [
            {
              university: '中山大学',
              major: '计算机',
              estScore: 620,
              probability: 0.45,
              risk: '冲',
              riskType: 'high',
              reason: '历年分数线接近',
            },
          ],
          stable: [],
          safe: [],
          createdAt: '2026-07-01T10:00:00Z',
        }),
      });
    });

    await page.goto('/plans/' + planId);

    await expect(page.getByText('🚀 冲刺')).toBeVisible({ timeout: 8000 });
    await expect(page.getByText('🎯 稳妥')).toBeVisible();
    await expect(page.getByText('🛡️ 保底')).toBeVisible();
  });
});