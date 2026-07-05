interface Step {
  key: string;
  label: string;
  done: boolean;
}

interface Props {
  steps: Step[];
  currentStep?: string;
  className?: string;
  ariaLabel?: string;
}

export function ProgressSteps({ steps, currentStep, className = '', ariaLabel }: Props) {
  const totalDone = steps.filter((s) => s.done).length;

  return (
    <div
      className={`inline-flex items-center gap-1.5 text-xs ${className}`}
      role="progressbar"
      aria-label={ariaLabel ?? `Completed ${totalDone}/${steps.length} steps`}
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
                isDone ? 'bg-green-500' : isActive ? 'bg-blue-500 ring-2 ring-blue-200 dark:ring-blue-950' : 'bg-gray-200 dark:bg-gray-700'
              }`}
            />
            <span className={`${isActive ? 'text-blue-600 font-medium dark:text-blue-300' : isDone ? 'text-green-600 dark:text-green-300' : 'text-gray-400 dark:text-gray-500'}`}>
              {step.label}
            </span>
            {idx < steps.length - 1 && <span className="w-3 h-px bg-gray-200 dark:bg-gray-700" />}
          </span>
        );
      })}
    </div>
  );
}

export function InfoCollectionProgress({
  province,
  score,
  subjects,
  labels = {
    province: 'Province',
    score: 'Score',
    subjects: 'Subjects',
  },
  ariaLabel,
}: {
  province?: string;
  score?: number;
  subjects?: string[];
  labels?: {
    province: string;
    score: string;
    subjects: string;
  };
  ariaLabel?: string;
}) {
  const steps = [
    { key: 'province', label: labels.province, done: Boolean(province) },
    { key: 'score', label: labels.score, done: Boolean(score) },
    { key: 'subjects', label: labels.subjects, done: Boolean(subjects?.length) },
  ];

  const currentKey = !province ? 'province' : !score ? 'score' : !subjects?.length ? 'subjects' : undefined;

  return (
    <ProgressSteps
      steps={steps}
      currentStep={currentKey}
      ariaLabel={ariaLabel}
      className="bg-white/90 border border-gray-100 rounded-full px-3 py-1.5 shadow-sm dark:border-gray-800 dark:bg-gray-900/90"
    />
  );
}
