import type { Page, Route } from '@playwright/test';

export async function mockPlans(page: Page): Promise<void> {
  await page.route('**/api/plans', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        plans: [
          {
            id: 'plan-e2e-001',
            name: 'E2E 测试方案',
            rush: [
              {
                university: '中南大学',
                major: '计算机科学与技术',
                estScore: 615,
                probability: 0.62,
                risk: 'medium',
                riskType: 'rush',
                reason: 'E2E fixture plan for poster generation',
              },
            ],
            stable: [],
            safe: [],
            createdAt: '2026-07-07T00:00:00Z',
          },
        ],
        total: 1,
      }),
    });
  });
}

export async function mockLatestShareLink(page: Page): Promise<void> {
  await page.route('**/api/share-link/latest', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 'share-e2e-latest',
        planId: 'plan-e2e-001',
        resultType: 'review_result',
        createdAt: '2026-07-07T00:00:00Z',
        expiresAt: '2026-08-06T00:00:00Z',
      }),
    });
  });
}

export async function mockGenericApiFallback(page: Page): Promise<void> {
  const passthroughMockExclusions = new Set([
    '/api/plans',
    '/api/share-link',
    '/api/share-link/latest',
    '/api/poster/generate',
  ]);
  await page.route(
    (url) =>
      url.pathname.startsWith('/api/') &&
      !passthroughMockExclusions.has(url.pathname) &&
      !url.pathname.includes('/poster/'),
    async (route: Route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    },
  );
}
