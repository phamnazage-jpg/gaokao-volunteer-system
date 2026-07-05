import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/renderWithProviders';
import { ReviewFlow } from './ReviewFlow';

describe('ReviewFlow', () => {
  it('renders start form and disables submit without plan id', () => {
    renderWithProviders(
      <ReviewFlow
        planId=""
        reviewId={null}
        comment=""
        onPlanIdChange={vi.fn()}
        onCommentChange={vi.fn()}
        onStart={vi.fn()}
        onAction={vi.fn()}
      />,
    );

    expect(screen.getByRole('region', { name: '发起方案审核' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '提交审核' })).toBeDisabled();
  });

  it('renders start form with English labels', () => {
    renderWithProviders(
      <ReviewFlow
        planId=""
        reviewId={null}
        comment=""
        onPlanIdChange={vi.fn()}
        onCommentChange={vi.fn()}
        onStart={vi.fn()}
        onAction={vi.fn()}
      />,
      { locale: 'en-US' },
    );

    expect(screen.getByRole('region', { name: 'Start plan review' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Submit review' })).toBeDisabled();
  });

  it('emits plan id changes and start action', async () => {
    const handlePlanIdChange = vi.fn();
    const handleStart = vi.fn();
    const { user } = renderWithProviders(
      <ReviewFlow
        planId="plan-001"
        reviewId={null}
        comment=""
        onPlanIdChange={handlePlanIdChange}
        onCommentChange={vi.fn()}
        onStart={handleStart}
        onAction={vi.fn()}
      />,
    );

    await user.type(screen.getByLabelText('方案 ID'), 'A');
    await user.click(screen.getByRole('button', { name: '提交审核' }));

    expect(handlePlanIdChange).toHaveBeenCalledWith('plan-001A');
    expect(handleStart).toHaveBeenCalledOnce();
  });

  it('renders safe start failure copy without backend details', () => {
    renderWithProviders(
      <ReviewFlow
        planId="plan-001"
        reviewId={null}
        comment=""
        isStartError
        onPlanIdChange={vi.fn()}
        onCommentChange={vi.fn()}
        onStart={vi.fn()}
        onAction={vi.fn()}
      />,
      { locale: 'en-US' },
    );

    expect(screen.getByRole('alert')).toHaveTextContent('Unable to start the review. Check the plan ID and try again.');
    expect(screen.queryByText(/raw backend/i)).not.toBeInTheDocument();
  });

  it('renders status loading and safe refresh failure states', () => {
    renderWithProviders(
      <ReviewFlow
        planId="plan-001"
        reviewId="review-001"
        comment=""
        isStatusLoading
        isStatusError
        onPlanIdChange={vi.fn()}
        onCommentChange={vi.fn()}
        onStart={vi.fn()}
        onAction={vi.fn()}
      />,
      { locale: 'en-US' },
    );

    expect(screen.getByRole('region', { name: 'Review status panel' })).toHaveTextContent('Loading review status...');
    expect(screen.getByRole('alert')).toHaveTextContent('Unable to refresh review status. The latest known state may be outdated.');
  });

  it('renders status and LLM progress', () => {
    renderWithProviders(
      <ReviewFlow
        planId="plan-001"
        reviewId="review-001"
        comment=""
        status={{
          id: 'review-001',
          planId: 'plan-001',
          status: 'in_progress',
          reviewerId: null,
          comment: '正在审核',
          updatedAt: '2026-07-04T00:00:00.000Z',
        }}
        enhanceStatus={{
          planId: 'plan-001',
          status: 'processing',
          progress: 60,
          currentStep: '生成风险建议',
          updatedAt: '2026-07-04T00:00:01.000Z',
        }}
        onPlanIdChange={vi.fn()}
        onCommentChange={vi.fn()}
        onStart={vi.fn()}
        onAction={vi.fn()}
      />,
    );

    expect(screen.getByRole('region', { name: '审核状态面板' })).toHaveTextContent('审核中');
    expect(screen.getByRole('region', { name: 'LLM 增强面板' })).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { name: 'LLM 增强进度' })).toHaveAttribute('aria-valuenow', '60');
    expect(screen.getByText('生成风险建议')).toBeInTheDocument();
  });

  it('renders status and LLM progress with English chrome labels', () => {
    renderWithProviders(
      <ReviewFlow
        planId="plan-001"
        reviewId="review-001"
        comment=""
        status={{
          id: 'review-001',
          planId: 'plan-001',
          status: 'in_progress',
          reviewerId: null,
          comment: 'Reviewing',
          updatedAt: '2026-07-04T00:00:00.000Z',
        }}
        enhanceStatus={{
          planId: 'plan-001',
          status: 'processing',
          progress: 60,
          currentStep: 'Generating risk recommendations',
          updatedAt: '2026-07-04T00:00:01.000Z',
        }}
        onPlanIdChange={vi.fn()}
        onCommentChange={vi.fn()}
        onStart={vi.fn()}
        onAction={vi.fn()}
      />,
      { locale: 'en-US' },
    );

    expect(screen.getByRole('region', { name: 'Review status panel' })).toHaveTextContent('In review');
    expect(screen.getByRole('region', { name: 'LLM enhancement panel' })).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { name: 'LLM enhancement progress' })).toHaveAttribute('aria-valuenow', '60');
  });

  it('requires comment for reject and request changes actions', async () => {
    const handleCommentChange = vi.fn();
    const handleAction = vi.fn();
    const { user } = renderWithProviders(
      <ReviewFlow
        planId="plan-001"
        reviewId="review-001"
        comment=""
        status={{
          id: 'review-001',
          planId: 'plan-001',
          status: 'pending',
          reviewerId: null,
          comment: null,
          updatedAt: '2026-07-04T00:00:00.000Z',
        }}
        onPlanIdChange={vi.fn()}
        onCommentChange={handleCommentChange}
        onStart={vi.fn()}
        onAction={handleAction}
      />,
    );

    expect(screen.getByRole('button', { name: '需修改' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '驳回' })).toBeDisabled();

    await user.type(screen.getByLabelText('审核意见（驳回 / 需修改时必填）'), '需要补充材料');
    await user.click(screen.getByRole('button', { name: '通过' }));

    expect(handleCommentChange).toHaveBeenCalledWith('需');
    expect(handleAction).toHaveBeenCalledWith('approve');
  });

  it('renders action controls with English labels', async () => {
    const handleCommentChange = vi.fn();
    const handleAction = vi.fn();
    const { user } = renderWithProviders(
      <ReviewFlow
        planId="plan-001"
        reviewId="review-001"
        comment="Needs details"
        status={{
          id: 'review-001',
          planId: 'plan-001',
          status: 'pending',
          reviewerId: null,
          comment: null,
          updatedAt: '2026-07-04T00:00:00.000Z',
        }}
        onPlanIdChange={vi.fn()}
        onCommentChange={handleCommentChange}
        onStart={vi.fn()}
        onAction={handleAction}
      />,
      { locale: 'en-US' },
    );

    expect(screen.getByRole('region', { name: 'Review actions' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Request changes' }));

    expect(handleAction).toHaveBeenCalledWith('request_changes');
  });

  it('renders safe action failure copy without backend details', () => {
    renderWithProviders(
      <ReviewFlow
        planId="plan-001"
        reviewId="review-001"
        comment="Needs details"
        status={{
          id: 'review-001',
          planId: 'plan-001',
          status: 'pending',
          reviewerId: null,
          comment: null,
          updatedAt: '2026-07-04T00:00:00.000Z',
        }}
        isActionError
        onPlanIdChange={vi.fn()}
        onCommentChange={vi.fn()}
        onStart={vi.fn()}
        onAction={vi.fn()}
      />,
      { locale: 'en-US' },
    );

    expect(screen.getByRole('alert')).toHaveTextContent('Unable to submit this review action. Please try again.');
    expect(screen.queryByText(/stack trace/i)).not.toBeInTheDocument();
  });
});
