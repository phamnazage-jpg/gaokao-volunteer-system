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

  it('renders review page and progress chrome with English labels', async () => {
    server.use(
      http.post('/api/review/start', () => {
        return HttpResponse.json({
          id: 'review-llm-en',
          planId: 'plan-llm-en',
          status: 'in_progress',
          reviewerId: null,
          comment: null,
          updatedAt: '2026-07-04T00:00:00.000Z',
        });
      }),
      http.get('/api/review/review-llm-en/status', () => {
        return HttpResponse.json({
          id: 'review-llm-en',
          planId: 'plan-llm-en',
          status: 'in_progress',
          reviewerId: null,
          comment: null,
          updatedAt: '2026-07-04T00:00:00.000Z',
        });
      }),
      http.get('/api/llm/enhance/plan-llm-en/status', () => {
        return HttpResponse.json({
          planId: 'plan-llm-en',
          status: 'processing',
          progress: 60,
          currentStep: 'Generating risk recommendations',
          updatedAt: '2026-07-04T00:00:01.000Z',
        });
      }),
    );

    renderWithProviders(<ReviewPage />, { locale: 'en-US' });

    expect(screen.getByRole('heading', { name: 'Plan review' })).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText('Plan ID'), 'plan-llm-en');
    await userEvent.click(screen.getByRole('button', { name: 'Submit review' }));

    const progress = await screen.findByRole('progressbar', { name: 'LLM enhancement progress' });
    expect(progress).toHaveAttribute('aria-valuenow', '60');
    expect(screen.getByText('Generating risk recommendations')).toBeInTheDocument();
  });

  it('uses safe copy when review start fails', async () => {
    server.use(
      http.post('/api/review/start', () => {
        return HttpResponse.json({ message: 'raw backend stack trace' }, { status: 500 });
      }),
    );

    renderWithProviders(<ReviewPage />, { locale: 'en-US' });

    await userEvent.type(screen.getByLabelText('Plan ID'), 'plan-error');
    await userEvent.click(screen.getByRole('button', { name: 'Submit review' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to start the review. Check the plan ID and try again.');
    expect(screen.queryByText(/raw backend stack trace/i)).not.toBeInTheDocument();
  });

  it('uses safe copy when review action fails', async () => {
    server.use(
      http.post('/api/review/start', () => {
        return HttpResponse.json({
          id: 'review-action-error',
          planId: 'plan-action-error',
          status: 'pending',
          reviewerId: null,
          comment: null,
          updatedAt: '2026-07-04T00:00:00.000Z',
        });
      }),
      http.get('/api/review/review-action-error/status', () => {
        return HttpResponse.json({
          id: 'review-action-error',
          planId: 'plan-action-error',
          status: 'pending',
          reviewerId: null,
          comment: null,
          updatedAt: '2026-07-04T00:00:00.000Z',
        });
      }),
      http.post('/api/review/action', () => {
        return HttpResponse.json({ message: 'raw action stack trace' }, { status: 500 });
      }),
      http.get('/api/llm/enhance/plan-action-error/status', () => {
        return HttpResponse.json({
          planId: 'plan-action-error',
          status: 'processing',
          progress: 25,
          currentStep: 'Generating risk recommendations',
          updatedAt: '2026-07-04T00:00:01.000Z',
        });
      }),
    );

    renderWithProviders(<ReviewPage />, { locale: 'en-US' });

    await userEvent.type(screen.getByLabelText('Plan ID'), 'plan-action-error');
    await userEvent.click(screen.getByRole('button', { name: 'Submit review' }));
    await screen.findByRole('region', { name: 'Review actions' });
    await userEvent.click(screen.getByRole('button', { name: 'Approve' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to submit this review action. Please try again.');
    expect(screen.queryByText(/raw action stack trace/i)).not.toBeInTheDocument();
  });
});
