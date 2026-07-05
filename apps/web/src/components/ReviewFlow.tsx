import { AlertCircle, CheckCircle, ShieldCheck, XCircle } from 'lucide-react';
import { FormattedMessage, useIntl } from 'react-intl';
import type { AuditEnhanceStatusResponse } from '@/hooks/useLLMEnhanceMutation';
import type { ReviewActionInput, ReviewStatusResponse } from '@/hooks/useReviewFlow';
import { LLMEnhancement } from '@/components/LLMEnhancement';

type ReviewActionType = ReviewActionInput['action'];
type ReviewStatus = ReviewStatusResponse['status'];

const STATUS_META: Record<ReviewStatus, { labelKey: string; icon: typeof AlertCircle; color: string }> = {
  pending: { labelKey: 'reviewFlow.status.pending', icon: AlertCircle, color: 'text-yellow-500' },
  in_progress: { labelKey: 'reviewFlow.status.inProgress', icon: ShieldCheck, color: 'text-blue-500' },
  approved: { labelKey: 'reviewFlow.status.approved', icon: CheckCircle, color: 'text-green-500' },
  rejected: { labelKey: 'reviewFlow.status.rejected', icon: XCircle, color: 'text-red-500' },
  changes_requested: { labelKey: 'reviewFlow.status.changesRequested', icon: AlertCircle, color: 'text-orange-500' },
};

interface ReviewFlowProps {
  planId: string;
  reviewId: string | null;
  comment: string;
  status?: ReviewStatusResponse;
  enhanceStatus?: AuditEnhanceStatusResponse;
  isStarting?: boolean;
  isStartError?: boolean;
  isStatusLoading?: boolean;
  isStatusError?: boolean;
  isActing?: boolean;
  isActionError?: boolean;
  onPlanIdChange: (planId: string) => void;
  onCommentChange: (comment: string) => void;
  onStart: () => void;
  onAction: (action: ReviewActionType) => void;
}

export function ReviewFlow({
  planId,
  reviewId,
  comment,
  status,
  enhanceStatus,
  isStarting = false,
  isStartError = false,
  isStatusLoading = false,
  isStatusError = false,
  isActing = false,
  isActionError = false,
  onPlanIdChange,
  onCommentChange,
  onStart,
  onAction,
}: ReviewFlowProps) {
  const intl = useIntl();

  if (!reviewId) {
    return (
      <section
        className="mt-6 rounded-xl border border-gray-100 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900"
        aria-label={intl.formatMessage({ id: 'reviewFlow.start.ariaLabel' })}
      >
        <label className="flex flex-col gap-2">
          <span className="text-sm text-gray-700 dark:text-gray-300">
            <FormattedMessage id="reviewFlow.start.planId" />
          </span>
          <input
            type="text"
            value={planId}
            onChange={(event) => onPlanIdChange(event.target.value)}
            placeholder={intl.formatMessage({ id: 'reviewFlow.start.planIdPlaceholder' })}
            className="min-h-[48px] rounded-lg border border-gray-200 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
          />
        </label>
        <button
          type="button"
          onClick={onStart}
          disabled={isStarting || !planId.trim()}
          className="mt-4 min-h-[48px] w-full rounded-xl bg-blue-600 py-3 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          <FormattedMessage id={isStarting ? 'reviewFlow.start.submitting' : 'reviewFlow.start.submit'} />
        </button>
        {isStartError && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200" role="alert">
            <FormattedMessage id="reviewFlow.error.start" />
          </div>
        )}
      </section>
    );
  }

  const canAct = status?.status === 'pending' || status?.status === 'in_progress';

  return (
    <div className="mt-6 space-y-4">
      {isStatusLoading && !status && (
        <section
          className="rounded-xl border border-gray-100 bg-white p-6 text-sm text-gray-600 shadow-sm dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300"
          aria-label={intl.formatMessage({ id: 'reviewFlow.statusPanel.ariaLabel' })}
          aria-busy="true"
        >
          <FormattedMessage id="reviewFlow.status.loading" />
        </section>
      )}

      {isStatusError && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200" role="alert">
          <FormattedMessage id="reviewFlow.error.status" />
        </div>
      )}

      {status && (
        <section
          className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900"
          aria-label={intl.formatMessage({ id: 'reviewFlow.statusPanel.ariaLabel' })}
        >
          <div className="flex items-center gap-2">
            {(() => {
              const Icon = STATUS_META[status.status].icon;
              return <Icon className={`h-6 w-6 ${STATUS_META[status.status].color}`} aria-hidden="true" />;
            })()}
            <div>
              <p className="text-xs text-gray-400 dark:text-gray-500">
                <FormattedMessage id="reviewFlow.statusPanel.label" />
              </p>
              <p className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                <FormattedMessage id={STATUS_META[status.status].labelKey} />
              </p>
            </div>
          </div>
          {status.comment && <p className="mt-3 rounded-lg bg-gray-50 p-3 text-sm text-gray-600 dark:bg-gray-800 dark:text-gray-300">{status.comment}</p>}
        </section>
      )}

      {enhanceStatus && (
        <LLMEnhancement planId={status?.planId ?? null} status={enhanceStatus} />
      )}

      {canAct && (
        <section
          className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900"
          aria-label={intl.formatMessage({ id: 'reviewFlow.actions.ariaLabel' })}
        >
          <label className="flex flex-col gap-2">
            <span className="text-sm text-gray-700 dark:text-gray-300">
              <FormattedMessage id="reviewFlow.actions.commentLabel" />
            </span>
            <textarea value={comment} onChange={(event) => onCommentChange(event.target.value)} rows={3} className="rounded-lg border border-gray-200 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100" />
          </label>
          <div className="mt-3 grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => onAction('approve')}
              disabled={isActing}
              className="min-h-[48px] rounded-xl bg-green-600 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              <FormattedMessage id="reviewFlow.actions.approve" />
            </button>
            <button
              type="button"
              onClick={() => onAction('request_changes')}
              disabled={isActing || !comment.trim()}
              className="min-h-[48px] rounded-xl bg-orange-500 py-2 text-sm font-medium text-white hover:bg-orange-600 disabled:opacity-50"
            >
              <FormattedMessage id="reviewFlow.actions.requestChanges" />
            </button>
            <button
              type="button"
              onClick={() => onAction('reject')}
              disabled={isActing || !comment.trim()}
              className="min-h-[48px] rounded-xl bg-red-600 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
            >
              <FormattedMessage id="reviewFlow.actions.reject" />
            </button>
          </div>
          {isActionError && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200" role="alert">
              <FormattedMessage id="reviewFlow.error.action" />
            </div>
          )}
        </section>
      )}
    </div>
  );
}
