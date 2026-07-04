/**
 * V10 · Sprint 4 · T-B-23.2 · e2e: chat send/receive (真实业务流)
 *
 * 覆盖：发送 → 流式 SSE → markdown 渲染
 */
import { test, expect } from '@playwright/test';

test.describe('Chat Send/Receive (V10 Sprint 4 · T-B-23.2)', () => {
  test('user sends message and receives streamed assistant response', async ({ page }) => {
    // 拦截后端流式接口，按 SSE 协议返回
    await page.route('**/api/chat/stream', async (route) => {
      const req = route.request();
      const body = req.postDataJSON() as { message?: string } | null;
      const userText = body?.message ?? '';
      const replyText = `关于「${userText}」，我会逐步帮你梳理。`;

      // 一次性发完，避免 ReadableStream 在 Playwright route.fulfill 上有兼容问题
      const sse = `data: ${JSON.stringify({ content: '你好！' })}\n\n` +
                  `data: ${JSON.stringify({ content: replyText })}\n\n`;
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: Buffer.from(sse, 'utf-8'),
      });
    });

    await page.route((url) => url.pathname.startsWith('/api/') && !url.pathname.includes('/chat/stream'), async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    });

    await page.goto('/');

    const input = page.getByRole('textbox', { name: '输入你的问题' });
    await expect(input).toBeVisible();

    await input.fill('广东省物理类 620 分');
    await input.press('Enter');

    // 用户消息立即出现
    await expect(page.getByText('广东省物理类 620 分').first()).toBeVisible();

    // 流式响应渲染（按 SSE content 字段解析，会拼接成 markdown）
    await expect(page.getByText(/关于「广东省物理类 620 分」，我会逐步帮你梳理/)).toBeVisible({ timeout: 8000 });
  });

  test('empty input does not trigger send', async ({ page }) => {
    await page.goto('/');

    const sendBtn = page.getByRole('button', { name: /请先输入内容|发送消息/ });
    await expect(sendBtn).toBeDisabled();
  });

  test('Shift+Enter inserts newline instead of sending', async ({ page }) => {
    await page.route('**/api/chat/stream', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    });

    await page.goto('/');
    const input = page.getByRole('textbox', { name: '输入你的问题' });
    await input.fill('第一行');
    await input.press('Shift+Enter');
    await input.type('第二行');

    const value = await input.inputValue();
    expect(value).toContain('第一行');
    expect(value).toContain('第二行');
    expect(value.split('\n').length).toBeGreaterThanOrEqual(2);
  });
});