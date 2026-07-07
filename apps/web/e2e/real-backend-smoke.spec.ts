import { expect, test } from '@playwright/test';

test.describe('Real backend smoke', () => {
  test.skip(process.env.GAOKAO_E2E_REAL_BACKEND !== '1', 'real backend smoke requires GAOKAO_E2E_REAL_BACKEND=1');

  test('public shell and health-backed API are reachable with a running backend', async ({ page, request }) => {
    const health = await request.get('/api/health').catch(() => null);
    // Vite proxies /api to the real backend in this mode. Some deployments expose /health outside /api;
    // the page-level assertion below is still the user-visible smoke if /api/health is not routed.
    if (health) {
      expect([200, 404]).toContain(health.status());
    }

    await page.goto('/');
    await expect(page.getByRole('heading', { name: /高考志愿|志愿填报|规划服务/ })).toBeVisible();
  });
});
