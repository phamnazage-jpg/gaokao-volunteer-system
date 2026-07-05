import { expect, test, type Locator, type Page } from '@playwright/test';

async function expectKeyboardFocus(locator: Locator): Promise<void> {
  await locator.focus();
  await expect(locator).toBeFocused();

  const outlineVisible = await locator.evaluate((element) => {
    const style = window.getComputedStyle(element);
    return style.outlineStyle !== 'none' || style.boxShadow !== 'none';
  });

  expect(outlineVisible).toBe(true);
}

async function seedAdminSession(page: Page): Promise<void> {
  await page.addInitScript(() => {
    window.localStorage.setItem(
      'gaokao-user-store',
      JSON.stringify({
        state: {
          id: 'admin-a11y',
          name: 'Runtime Admin',
          phone: '13800138000',
          role: 'admin',
          isLoggedIn: true,
        },
        version: 0,
      }),
    );
  });
}

test.describe('Runtime accessibility smoke (non-Docker)', () => {
  test('public shell exposes landmarks, named controls, focus rings, and dark mode', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByRole('main').or(page.locator('.app-layout'))).toBeVisible();
    expect(await page.getByRole('navigation').count()).toBeGreaterThanOrEqual(1);
    await expect(page.getByRole('navigation').first()).toBeVisible();
    const chatInput = page.getByRole('textbox', { name: /输入你的问题|Enter your question/ });
    await expect(chatInput).toBeVisible();

    await expectKeyboardFocus(chatInput);
    await page.getByRole('radio', { name: '暗色' }).click();
    await expect(page.locator('html')).toHaveClass(/dark/);
  });

  test('data query page keeps labelled form controls and methodology dialog semantics', async ({ page }) => {
    await page.goto('/data-query');

    await expect(page.getByRole('heading', { name: /数据查询|Data query/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /数据口径|Methodology/ })).toBeVisible();
    await expect(page.getByLabel(/省份|Province/).first()).toBeVisible();
    await expect(page.getByLabel(/年份|Year/).first()).toBeVisible();

    await page.getByRole('button', { name: /数据口径|Methodology/ }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('button', { name: /关闭|Close/ })).toBeVisible();
  });

  test('admin login and protected layout expose runtime accessibility landmarks', async ({ page }) => {
    await page.goto('/admin/login');

    await expect(page.getByRole('main')).toBeVisible();
    await expect(page.getByLabel(/手机号|Phone/)).toBeVisible();
    await expect(page.getByLabel(/验证码|Code/)).toBeVisible();
    await expectKeyboardFocus(page.getByLabel(/手机号|Phone/));

    await seedAdminSession(page);
    await page.goto('/admin');

    await expect(page.getByRole('navigation', { name: /后台导航|Admin navigation/ })).toBeVisible();
    await expect(page.getByRole('main')).toBeVisible();
    await expect(page.getByRole('button', { name: /退出|Logout/ })).toBeVisible();
  });
});
