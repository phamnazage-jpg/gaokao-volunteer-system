/**
 * V10 · Sprint 3 · share-link e2e
 * 验证分享管理页 + 弹窗 + 链接展示
 */
import { test, expect } from '@playwright/test';

test.describe('Share Link (V10 Sprint 3 · T-B-28)', () => {
  test('share dialog page renders + opens dialog', async ({ page }) => {
    // 拦截所有 /api/** 返回空数据
    await page.route('**/api/**', async (route) => {
      const url = route.request().url();
      if (url.includes('portal/share-link/latest')) {
        await route.fulfill({ status: 200, contentType: 'application/json', body: 'null' });
      } else {
        await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
      }
    });

    await page.goto('/share');
    await expect(page.getByRole('heading', { name: '分享管理' })).toBeVisible();
    await expect(page.getByText('暂无分享链接')).toBeVisible();

    // 点击外部创建按钮 → 打开弹窗
    await page.getByRole('button', { name: '创建第一个分享链接' }).click();
    await expect(page.getByRole('dialog', { name: '分享方案' })).toBeVisible();
    await expect(page.getByText('示例方案：广东物理 620 冲刺院校')).toBeVisible();

    // 弹窗内的 CTA
    await expect(page.getByRole('button', { name: /生成分享海报/ })).toBeVisible();
  });
});