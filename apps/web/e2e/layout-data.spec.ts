/**
 * V10 选项 B · e2e: layout data binding
 *
 * 覆盖 AppLayout 不再用本地消息临时拼 recentChat，改为读取咨询记录 API。
 */
import { test, expect } from '@playwright/test';

test.describe('Layout data binding', () => {
  test('desktop sidebar renders recent consultations from API data', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });

    await page.route('**/api/consultations**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          consultations: [
            {
              id: 'consultation-e2e-1',
              title: '真实咨询记录入口',
              messageCount: 3,
              createdAt: '2026-07-03T00:00:00.000Z',
              updatedAt: '2026-07-03T00:05:00.000Z',
            },
          ],
          total: 1,
        }),
      });
    });

    await page.goto('/');
    await page.waitForResponse((response) => response.url().includes('/api/consultations') && response.status() === 200);

    await expect(page.getByRole('heading', { name: '最近对话' })).toBeVisible();
    await expect(page.getByRole('button', { name: '真实咨询记录入口' })).toBeVisible();
  });
});
