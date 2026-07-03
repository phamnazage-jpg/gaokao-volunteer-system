/**
 * V10 选项 B · ProgressSteps 组件
 * 移除 'use client' (Vite 不需要) + 替换 brand-* 颜色为 Tailwind 4
 */

interface Step {
  key: string;
  label: string;
  done: boolean;
}

interface Props {
  steps: Step[];
  currentStep?: string;
  className?: string;
}

export function ProgressSteps({ steps, currentStep, className = '' }: Props) {
  const totalDone = steps.filter((s) => s.done).length;

  return (
    <div
      className={`inline-flex items-center gap-1.5 text-xs ${className}`}
      role="progressbar"
      aria-label={`已完成 ${totalDone}/${steps.length} 步`}
      aria-valuenow={totalDone}
      aria-valuemin={0}
      aria-valuemax={steps.length}
    >
      {steps.map((step, idx) => {
        const isDone = step.done;
        const isActive = step.key === currentStep;

        return (
          <span key={step.key} className="inline-flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full transition-colors ${
                isDone ? 'bg-green-500' : isActive ? 'bg-blue-500 ring-2 ring-blue-200' : 'bg-gray-200'
              }`}
            />
            <span className={`${isActive ? 'text-blue-600 font-medium' : isDone ? 'text-green-600' : 'text-gray-400'}`}>
              {step.label}
            </span>
            {idx < steps.length - 1 && <span className="w-3 h-px bg-gray-200" />}
          </span>
        );
      })}
    </div>
  );
}

/**
 * 信息收集进度 — 预置步骤
 */
export function InfoCollectionProgress({
  province,
  score,
  subjects,
}: {
  province?: string;
  score?: number;
  subjects?: string[];
}) {
  const steps = [
    { key: 'province', label: '省份', done: Boolean(province) },
    { key: 'score', label: '分数', done: Boolean(score) },
    { key: 'subjects', label: '选科', done: Boolean(subjects?.length) },
  ];

  const currentKey = !province ? 'province' : !score ? 'score' : !subjects?.length ? 'subjects' : undefined;

  return (
    <ProgressSteps
      steps={steps}
      currentStep={currentKey}
      className="bg-white/90 border border-gray-100 rounded-full px-3 py-1.5 shadow-sm"
    />
  );
}