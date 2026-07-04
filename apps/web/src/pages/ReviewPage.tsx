/**
 * V10 · Sprint 3 · ReviewPage
 * 审核流页：发起审核 + 轮询状态 + 审核操作
 */
import { useState } from 'react';
import { ShieldCheck, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import {
  useReviewStartMutation,
  useReviewStatusQuery,
  useReviewActionMutation,
} from '@/hooks/useReviewFlow';
import { useAuditEnhanceStatusQuery } from '@/hooks/useLLMEnhanceMutation';

const STATUS_META = {
  pending: { label: '等待中', icon: AlertCircle, color: 'text-yellow-500' },
  in_progress: { label: '审核中', icon: ShieldCheck, color: 'text-blue-500' },
  approved: { label: '已通过', icon: CheckCircle, color: 'text-green-500' },
  rejected: { label: '已驳回', icon: XCircle, color: 'text-red-500' },
  changes_requested: { label: '需修改', icon: AlertCircle, color: 'text-orange-500' },
} as const;

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
      <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
        <ShieldCheck className="w-6 h-6" aria-hidden="true" />
        方案审核
      </h1>

      {!reviewId ? (
        <div className="mt-6 rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
          <label className="flex flex-col gap-2">
            <span className="text-sm text-gray-700">方案 ID</span>
            <input
              type="text"
              value={planId}
              onChange={(e) => setPlanId(e.target.value)}
              placeholder="例如：plan-001"
              className="px-3 py-2 rounded-lg border border-gray-200 text-sm min-h-[48px]"
            />
          </label>
          <button
            type="button"
            onClick={handleStart}
            disabled={start.isPending || !planId.trim()}
            className="mt-4 w-full min-h-[48px] py-3 rounded-xl bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {start.isPending ? '提交中…' : '提交审核'}
          </button>
        </div>
      ) : (
        <div className="mt-6 space-y-4">
          {status.data && (
            <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-2">
                {(() => {
                  const Icon = STATUS_META[status.data.status].icon;
                  return <Icon className={`w-6 h-6 ${STATUS_META[status.data.status].color}`} aria-hidden="true" />;
                })()}
                <div>
                  <p className="text-xs text-gray-400">审核状态</p>
                  <p className="text-lg font-semibold text-gray-800">
                    {STATUS_META[status.data.status].label}
                  </p>
                </div>
              </div>
              {status.data.comment && (
                <p className="mt-3 text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                  {status.data.comment}
                </p>
              )}
            </div>
          )}

          {enhanceStatus.data && (
            <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs text-gray-400">LLM 增强</p>
                  <p className="text-sm font-medium text-gray-800">{enhanceStatus.data.currentStep}</p>
                </div>
                <p className="text-sm font-semibold text-blue-700">{enhanceStatus.data.progress}%</p>
              </div>
              <div
                className="mt-3 h-2 rounded-full bg-gray-100"
                role="progressbar"
                aria-label="LLM 增强进度"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={enhanceStatus.data.progress}
              >
                <div
                  className="h-full rounded-full bg-blue-600 transition-[width]"
                  style={{ width: `${enhanceStatus.data.progress}%` }}
                />
              </div>
            </div>
          )}

          {status.data?.status === 'pending' || status.data?.status === 'in_progress' ? (
            <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
              <label className="flex flex-col gap-2">
                <span className="text-sm text-gray-700">审核意见（驳回 / 需修改时必填）</span>
                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  rows={3}
                  className="px-3 py-2 rounded-lg border border-gray-200 text-sm"
                />
              </label>
              <div className="mt-3 grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => handleAction('approve')}
                  disabled={action.isPending}
                  className="min-h-[48px] py-2 rounded-xl bg-green-600 text-white text-sm font-medium hover:bg-green-700 disabled:opacity-50"
                >
                  通过
                </button>
                <button
                  type="button"
                  onClick={() => handleAction('request_changes')}
                  disabled={action.isPending || !comment.trim()}
                  className="min-h-[48px] py-2 rounded-xl bg-orange-500 text-white text-sm font-medium hover:bg-orange-600 disabled:opacity-50"
                >
                  需修改
                </button>
                <button
                  type="button"
                  onClick={() => handleAction('reject')}
                  disabled={action.isPending || !comment.trim()}
                  className="min-h-[48px] py-2 rounded-xl bg-red-600 text-white text-sm font-medium hover:bg-red-700 disabled:opacity-50"
                >
                  驳回
                </button>
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
