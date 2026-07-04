/**
 * Sprint 4 T-B-42 · LLM 增强进度轮询
 */
import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { ReviewPage } from './ReviewPage';
import { renderWithProviders } from '@/test/renderWithProviders';
import { server } from '@/test/mocks/server';

describe('ReviewPage', () => {
  it('renders LLM enhance progress after review starts', async () => {
    server.use(
      http.post('/api/review/start', () => {
        return HttpResponse.json({
          id: 'review-llm-1',
          planId: 'plan-llm-1',
          status: 'in_progress',
          reviewerId: null,
          comment: null,
          updatedAt: '2026-07-04T00:00:00.000Z',
        });
      }),
      http.get('/api/review/review-llm-1/status', () => {
        return HttpResponse.json({
          id: 'review-llm-1',
          planId: 'plan-llm-1',
          status: 'in_progress',
          reviewerId: null,
          comment: null,
          updatedAt: '2026-07-04T00:00:00.000Z',
        });
      }),
      http.get('/api/llm/enhance/plan-llm-1/status', () => {
        return HttpResponse.json({
          planId: 'plan-llm-1',
          status: 'processing',
          progress: 60,
          currentStep: '生成风险建议',
          updatedAt: '2026-07-04T00:00:01.000Z',
        });
      }),
    );

    renderWithProviders(<ReviewPage />);

    await userEvent.type(screen.getByLabelText('方案 ID'), 'plan-llm-1');
    await userEvent.click(screen.getByRole('button', { name: '提交审核' }));

    const progress = await screen.findByRole('progressbar', { name: 'LLM 增强进度' });
    expect(progress).toHaveAttribute('aria-valuenow', '60');
    expect(screen.getByText('生成风险建议')).toBeInTheDocument();
  });
});
