import { useState } from 'react';
import { ShieldCheck } from 'lucide-react';
import { FormattedMessage } from 'react-intl';
import {
  useReviewStartMutation,
  useReviewStatusQuery,
  useReviewActionMutation,
} from '@/hooks/useReviewFlow';
import { useAuditEnhanceStatusQuery } from '@/hooks/useLLMEnhanceMutation';
import { ReviewFlow } from '@/components/ReviewFlow';

export function ReviewPage() {
  const [planId, setPlanId] = useState('');
  const [reviewId, setReviewId] = useState<string | null>(null);
  const [comment, setComment] = useState('');

  const start = useReviewStartMutation();
  const status = useReviewStatusQuery(reviewId);
  const enhancePlanId = status.data?.planId ?? start.data?.planId ?? null;
  const enhanceStatus = useAuditEnhanceStatusQuery(enhancePlanId);
  const action = useReviewActionMutation();

  const handleStart = (): void => {
    if (!planId.trim()) return;
    start.mutate({ planId: planId.trim() }, {
      onSuccess: (data) => setReviewId(data.id),
    });
  };

  const handleAction = (actionType: 'approve' | 'reject' | 'request_changes'): void => {
    if (!reviewId) return;
    action.mutate({ action: actionType, reviewId, comment });
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2 dark:text-gray-100">
        <ShieldCheck className="w-6 h-6" aria-hidden="true" />
        <FormattedMessage id="reviewPage.title" />
      </h1>

      <ReviewFlow
        planId={planId}
        reviewId={reviewId}
        comment={comment}
        status={status.data}
        enhanceStatus={enhanceStatus.data}
        isStarting={start.isPending}
        isStartError={start.isError}
        isStatusLoading={status.isLoading}
        isStatusError={status.isError}
        isActing={action.isPending}
        isActionError={action.isError}
        onPlanIdChange={setPlanId}
        onCommentChange={setComment}
        onStart={handleStart}
        onAction={handleAction}
      />
    </div>
  );
}
