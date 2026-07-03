import { expect, test } from '@playwright/test';

test.describe('Offline degradation', () => {
  test('shows a 48px offline banner and hides it after network recovery', async ({ context, page }) => {
    await page.goto('/');

    await context.setOffline(true);
    await page.evaluate(() => window.dispatchEvent(new Event('offline')));

    const banner = page.getByRole('status', { name: '离线状态' });
    await expect(banner).toBeVisible();
    await expect(banner).toContainText('当前处于离线状态');

    const bannerBox = await banner.boundingBox();
    expect(bannerBox?.height).toBeGreaterThanOrEqual(48);

    await context.setOffline(false);
    await page.evaluate(() => window.dispatchEvent(new Event('online')));

    await expect(banner).toBeHidden();
  });
});
