/**
 * V10 选项 B · e2e: theme switch (暗/亮/系统)
 *
 * V10 不变量 D2
 */
import { test, expect } from '@playwright/test';

test.describe('Theme Switch (V10 不变量 D2)', () => {
  test('三主题切换 + 持久化', async ({ page }) => {
    await page.goto('/');

    // 初始: system 主题 (跟系统)
    const html = page.locator('html');
    await expect(html).toHaveClass(/light|dark/);

    // 点击亮色主题
    await page.getByRole('radio', { name: '亮色' }).click();
    await expect(html).toHaveClass(/light/);

    // 刷新页面, 主题保持
    await page.reload();
    await expect(html).toHaveClass(/light/);

    // 切换暗色
    await page.getByRole('radio', { name: '暗色' }).click();
    await expect(html).toHaveClass(/dark/);
  });
});