/**
 * V10 选项 B · e2e: navigation (桌面三栏 / 移动 48px Tab)
 *
 * V10 不变量 L1 + L2
 */
import { test, expect } from '@playwright/test';

test.describe('Navigation (V10 不变量 L1 + L2)', () => {
  test('桌面 ≥ 1024px 显示侧栏', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/');

    const sidebar = page.locator('aside.sidebar');
    await expect(sidebar).toBeVisible();
  });

  test('移动 < 768px 显示 48px 底部 Tab', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    const mobileNav = page.getByRole('navigation', { name: '移动端导航' });
    await expect(mobileNav).toBeVisible();

    // 检查 min-height 48px
    await expect(mobileNav).toBeVisible();
    // 每个 Tab 元素高度 48px (来自 Tailwind class min-h-[48px])
    const tabs = mobileNav.locator('a');
    const firstTab = tabs.first();
    const tabBox = await firstTab.boundingBox();
    expect(tabBox?.height).toBeGreaterThanOrEqual(48);
  });

  test('桌面端点击 "我的方案" 跳转', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/');

    await page.getByRole('link', { name: /我的方案/ }).first().click();
    await expect(page).toHaveURL(/\/plans/);
    await expect(page.getByRole('heading', { name: '📋 我的方案' })).toBeVisible();
  });
});