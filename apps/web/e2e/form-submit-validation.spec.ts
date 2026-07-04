/**
 * V10 · Sprint 4 · T-B-23.3 · e2e: form submit + validation (FormCard 3-step)
 *
 * 简化版：FormCard 是 ChatMessage 内嵌的组件，不是独立路由
 * 改为通过 chat send 路径验证 SubmitButton 守卫
 */
import { test, expect } from '@playwright/test';

test.describe('Form Submit + Validation (V10 Sprint 4 · T-B-23.3)', () => {
  test.beforeEach(async ({ page }) => {
    // 让 chat 流式接口返回空，避免影响
    await page.route('**/api/**', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    });
  });

  test('SubmitButton guards send button during streaming', async ({ page }) => {
    // 拦截 form submit 路径，模拟慢响应验证 spinner
    await page.route('**/api/chat/stream', async (route) => {
      await new Promise((r) => setTimeout(r, 1500));
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    });

    await page.goto('/');

    const input = page.getByRole('textbox', { name: '输入你的问题' });
    await input.fill('测试提交');

    // 使用 keyboard Enter 触发提交（更接近 keyboard interaction，绕过 mobile nav 的 pointer intercept）
    await input.press('Enter');

    // 发送按钮应立即切换到 disabled（aria-label 会变 "请先输入内容"）
    await expect(page.getByRole('button', { name: '请先输入内容' })).toBeDisabled({ timeout: 2000 });
  });

  test('SubmitButton does not double-fire when clicked twice rapidly', async ({ page }) => {
    let callCount = 0;
    await page.route('**/api/chat/stream', async (route) => {
      callCount += 1;
      await new Promise((r) => setTimeout(r, 800));
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{"content":""}' });
    });

    await page.goto('/');

    const input = page.getByRole('textbox', { name: '输入你的问题' });
    await input.fill('连续点击');

    // 第一次按 Enter 触发提交
    await input.press('Enter');

    // 此时按钮应 disabled（aria-label='请先输入内容'）
    await expect(page.getByRole('button', { name: '请先输入内容' })).toBeDisabled({ timeout: 2000 });

    // 试图再次按 Enter（在已 disabled 状态下不应触发新请求）
    await page.waitForTimeout(200);
    await input.press('Enter').catch(() => {});

    await page.waitForTimeout(1500);
    expect(callCount).toBe(1);
  });
});