/**
 * V10 · Sprint 4 · T-B-41 · e2e: ShareLink failure fallback
 */
import { test, expect } from '@playwright/test';
import { mockGenericApiFallback, mockLatestShareLink } from './helpers/mock-api';

test.describe('Share Link failure fallback (V10 Sprint 4 · T-B-41)', () => {
  test('share dialog shows retryable fallback when create endpoint fails', async ({ page }) => {
    await mockLatestShareLink(page);

    await page.route((url) => url.pathname === '/api/share-link', async (route) => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'share service unavailable' }),
      });
    });

    await mockGenericApiFallback(page);

    await page.goto('/share');

    await expect(page.getByRole('heading', { name: '分享管理' })).toBeVisible();
    await page.getByRole('button', { name: /创建分享链接|新建分享链接/ }).click();
    await expect(page.getByRole('button', { name: '创建分享链接（30天有效）' })).toBeEnabled();
    await page.getByRole('button', { name: '创建分享链接（30天有效）' }).click();

    await expect(page.getByRole('alert').filter({ hasText: '分享链接创建失败' })).toBeVisible();
    await expect(page.getByRole('button', { name: '重试创建分享链接' })).toBeVisible();
  });
});
