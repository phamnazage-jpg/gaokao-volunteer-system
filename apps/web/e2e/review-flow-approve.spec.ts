/**
 * V10 · Sprint 4 · T-B-23.7 · e2e: review flow (审核流)
 *
 * ReviewPage 真实实现：planId input + start → 进入状态显示
 * 状态用 STATUS_META 标签：等待中/审核中/已通过/已驳回/需修改
 */
import { test, expect } from '@playwright/test';

test.describe('Review Flow (V10 Sprint 4 · T-B-23.7)', () => {
  test('review page starts with planId input', async ({ page }) => {
    await page.route('**/api/**', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    });

    await page.goto('/review');
    await expect(page.getByRole('heading', { name: '方案审核' })).toBeVisible();
    await expect(page.getByPlaceholder(/plan-001|方案 ID/)).toBeVisible();
    await expect(page.getByRole('button', { name: /提交审核/ })).toBeVisible();
  });

  test('submitting review transitions to status display with action buttons', async ({ page }) => {
    await page.route('**/api/review/start', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'review-e2e-1',
          planId: 'plan-e2e-1',
          status: 'pending',
          reviewerId: null,
          comment: null,
          updatedAt: '2026-07-01T10:00:00Z',
        }),
      });
    });

    await page.route('**/api/review/review-e2e-1/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'review-e2e-1',
          planId: 'plan-e2e-1',
          status: 'pending',
          reviewerId: null,
          comment: null,
          updatedAt: '2026-07-01T10:00:00Z',
        }),
      });
    });

    await page.route('**/api/review/action', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'review-e2e-1',
          planId: 'plan-e2e-1',
          status: 'approved',
          reviewerId: 'reviewer-1',
          comment: '方案合理',
          updatedAt: '2026-07-01T10:05:00Z',
        }),
      });
    });

    await page.goto('/review');
    await page.getByPlaceholder(/plan-001|方案 ID/).fill('plan-e2e-1');
    await page.getByRole('button', { name: /提交审核/ }).click();

    // 状态显示："等待中"
    await expect(page.getByText('等待中')).toBeVisible({ timeout: 5000 });

    // 3 个操作按钮
    await expect(page.getByRole('button', { name: '通过' })).toBeVisible();
    await expect(page.getByRole('button', { name: '需修改' })).toBeDisabled();
    await expect(page.getByRole('button', { name: '驳回' })).toBeDisabled();

    // 填写意见 + 点击通过
    const textarea = page.getByRole('textbox').last();
    await textarea.fill('方案合理');
    await expect(page.getByRole('button', { name: '需修改' })).toBeEnabled();
    await page.getByRole('button', { name: '通过' }).click();
  });
});