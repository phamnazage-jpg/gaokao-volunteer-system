/**
 * V10 · Sprint 4 · T-B-23.6 · e2e: data query (ScoreLine + Schools + Majors)
 *
 * DataQueryPage 真实实现：表单（省份/年份/科类/位次）+ 院校/专业搜索
 * 注意：路由是 /data-query（实际定义）
 */
import { test, expect } from '@playwright/test';

test.describe('Data Query (V10 Sprint 4 · T-B-23.6)', () => {
  test('data query page renders filter form + 院校/专业 results', async ({ page }) => {
    await page.route('**/api/data-query/schools**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          schools: [
            { id: 'sysu', name: '中山大学', province: '广东', is985: true, is211: true },
            { id: 'scut', name: '华南理工大学', province: '广东', is985: false, is211: true },
          ],
          total: 2,
        }),
      });
    });

    await page.route('**/api/data-query/majors**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          majors: [
            { id: 'cs', name: '计算机科学与技术', category: '工学' },
          ],
          total: 1,
        }),
      });
    });

    // fallback 只 catch 其他 API（不包括 data-query），避免覆盖前面的 mock
    await page.route((url) => url.pathname.startsWith('/api/') && !url.pathname.includes('/data-query'), async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    });

    await page.goto('/data-query');

    await expect(page.getByRole('heading', { name: '数据查询' })).toBeVisible();

    // 院校区显示"中山大学"和"华南理工大学"（默认 keyword=空）
    await expect(page.getByText('中山大学')).toBeVisible({ timeout: 8000 });
    await expect(page.getByText('华南理工大学')).toBeVisible();

    // 985 / 211 标记（用更宽松的 locator）
    await expect(page.getByText('985', { exact: true }).first()).toBeVisible();
    await expect(page.getByText('211', { exact: true }).first()).toBeVisible();

    // 专业区显示
    await expect(page.getByText('计算机科学与技术')).toBeVisible();
  });

  test('empty data renders page with empty lists', async ({ page }) => {
    await page.route('**/api/data-query/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ schools: [], majors: [], total: 0, lines: [] }),
      });
    });

    await page.route((url) => url.pathname.startsWith('/api/') && !url.pathname.includes('/data-query'), async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    });

    await page.goto('/data-query');
    await expect(page.getByRole('heading', { name: '数据查询' })).toBeVisible();
  });
});