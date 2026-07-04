/**
 * V10 · Sprint 4 · T-B-23.1 · e2e: theme switch (3-mode persistence)
 *
 * V10 不变量 D2: light / dark / system
 * ThemeToggle 实现：3 个 radio 按钮 + 同步 localStorage['theme-pref']
 */
import { test, expect } from '@playwright/test';

test.describe('Theme Switch (V10 Sprint 4 · T-B-23.1 · V10 不变量 D2)', () => {
  test('3-theme switch + persistence', async ({ page }) => {
    await page.goto('/');

    const html = page.locator('html');

    // 切换到亮色
    await page.getByRole('radio', { name: '亮色' }).click();
    await expect(html).toHaveClass(/light/);
    await expect(page.getByRole('radio', { name: '亮色' })).toHaveAttribute('aria-checked', 'true');

    // 切换到暗色
    await page.getByRole('radio', { name: '暗色' }).click();
    await expect(html).toHaveClass(/dark/);
    await expect(page.getByRole('radio', { name: '暗色' })).toHaveAttribute('aria-checked', 'true');

    // 切换到跟随系统
    await page.getByRole('radio', { name: '系统' }).click();
    await expect(html).toHaveClass(/light|dark/);
    await expect(page.getByRole('radio', { name: '系统' })).toHaveAttribute('aria-checked', 'true');

    // localStorage 持久化
    const stored = await page.evaluate(() => localStorage.getItem('theme-pref'));
    expect(stored).toBe('system');

    // 刷新后保持
    await page.reload();
    await expect(page.getByRole('radio', { name: '系统' })).toHaveAttribute('aria-checked', 'true');
  });

  test('inline script prevents theme flash on first paint', async ({ page }) => {
    await page.goto('/');
    const htmlClass = await page.locator('html').getAttribute('class');
    expect(htmlClass).toMatch(/light|dark/);
  });
});