/**
 * V10 · Sprint 4 · T-B-23.8 · e2e: poster generate + download (真实存在的 UI)
 *
 * PosterPreviewPage 真实实现：3 模板（经典/现代/简约）+ 生成按钮 + 预览 img + 下载
 * 注意：路由 /poster（不是 /poster/:planId，因为页面写死 planId = 'plan-sample-001'）
 */
import { test, expect } from '@playwright/test';

test.describe('Poster Generate + Download (V10 Sprint 4 · T-B-23.8)', () => {
  test('poster page renders 3 templates + generates poster', async ({ page }) => {
    // 只 mock poster/generate，不要覆盖整个 /api/** （Playwright 多 handler 同时匹配时，
    // 第一个注册的会被先调用，所以不需要 return 来 skip — 只要不再注册 fallback 即可）
    await page.route('**/api/poster/generate', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          posterUrl: 'https://example.com/poster.png',
          qrCode: 'https://example.com/qr.png',
          expiresAt: '2026-08-01T00:00:00Z',
        }),
      });
    });

    // fallback 只 catch 其他 API（不包括 poster/generate）
    await page.route((url) => url.pathname.startsWith('/api/') && !url.pathname.includes('/poster/generate'), async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    });

    await page.goto('/poster');

    await expect(page.getByRole('heading', { name: '海报生成' })).toBeVisible();

    // 3 个模板按钮
    await expect(page.getByRole('button', { name: '经典' })).toBeVisible();
    await expect(page.getByRole('button', { name: '现代' })).toBeVisible();
    await expect(page.getByRole('button', { name: '简约' })).toBeVisible();

    // 选择"现代"
    await page.getByRole('button', { name: '现代' }).click();
    await expect(page.getByRole('button', { name: '现代' })).toHaveAttribute('aria-pressed', 'true');

    // 生成
    await page.getByRole('button', { name: /生成海报/ }).click();

    // 海报预览（src 是 url() 校验过的合法 URL）
    await expect(page.locator('img[alt="海报预览"]')).toBeVisible({ timeout: 8000 });
    await expect(page.locator('img[alt="海报预览"]')).toHaveAttribute('src', 'https://example.com/poster.png');

    // 下载链接 + 复制二维码
    await expect(page.locator('a[download]')).toBeVisible();
    await expect(page.getByRole('button', { name: '复制二维码' })).toBeVisible();
  });

  test('poster async job shows progress before preview', async ({ page }) => {
    let statusCalls = 0;
    await page.route('**/api/poster/generate', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobId: 'poster-e2e-async',
          status: 'queued',
          progress: 5,
          posterUrl: 'https://example.com/poster-placeholder.png',
          qrCode: 'https://example.com/qr.png',
          expiresAt: '2026-08-01T00:00:00Z',
        }),
      });
    });

    await page.route('**/api/poster/poster-e2e-async/status', async (route) => {
      statusCalls += 1;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          statusCalls === 1
            ? {
                jobId: 'poster-e2e-async',
                status: 'processing',
                progress: 40,
                posterUrl: null,
                qrCode: null,
                expiresAt: null,
                updatedAt: '2026-07-04T00:00:00Z',
              }
            : {
                jobId: 'poster-e2e-async',
                status: 'completed',
                progress: 100,
                posterUrl: 'https://example.com/poster-async.png',
                qrCode: 'https://example.com/qr.png',
                expiresAt: '2026-08-01T00:00:00Z',
                updatedAt: '2026-07-04T00:00:02Z',
              },
        ),
      });
    });

    await page.route((url) => url.pathname.startsWith('/api/') && !url.pathname.includes('/poster/'), async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    });

    await page.goto('/poster');
    await page.getByRole('button', { name: /生成海报/ }).click();

    await expect(page.getByRole('progressbar', { name: '海报生成进度' })).toHaveAttribute('aria-valuenow', '40');
    await expect(page.locator('img[alt="海报预览"]')).toHaveAttribute('src', 'https://example.com/poster-async.png', {
      timeout: 8000,
    });
  });

  test('poster shows no preview when generation fails (Zod 校验失败)', async ({ page }) => {
    // 返回非法 URL（不是 https）让 Zod url() 校验失败
    await page.route('**/api/poster/generate', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          posterUrl: 'invalid-url',
          qrCode: 'xxx',
          expiresAt: '2026-08-01T00:00:00Z',
        }),
      });
    });
    await page.route((url) => url.pathname.startsWith('/api/') && !url.pathname.includes('/poster/generate'), async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    });

    await page.goto('/poster');
    await page.getByRole('button', { name: /生成海报/ }).click();

    // 校验失败，posterUrl 不会写入 store，没有 img 渲染
    await page.waitForTimeout(3000);
    await expect(page.locator('img[alt="海报预览"]')).toHaveCount(0);
  });
});
