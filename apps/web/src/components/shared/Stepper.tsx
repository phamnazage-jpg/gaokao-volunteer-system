import { useIntl } from 'react-intl';

export interface StepperStep {
  key: string;
  label: string;
}

interface StepperProps {
  steps: StepperStep[];
  currentIndex: number;
  label?: string;
  className?: string;
}

function getStepState(index: number, currentIndex: number): 'complete' | 'current' | 'upcoming' {
  if (index < currentIndex) return 'complete';
  if (index === currentIndex) return 'current';
  return 'upcoming';
}

export function Stepper({ steps, currentIndex, label, className = '' }: StepperProps) {
  const intl = useIntl();
  const safeIndex = Math.min(Math.max(currentIndex, 0), Math.max(steps.length - 1, 0));
  const resolvedLabel = label ?? intl.formatMessage({ id: 'stepper.ariaLabel' });

  return (
    <ol
      className={`flex items-center justify-between ${className}`}
      aria-label={resolvedLabel}
      aria-valuenow={safeIndex + 1}
      aria-valuemin={1}
      aria-valuemax={steps.length}
    >
      {steps.map((step, index) => {
        const state = getStepState(index, safeIndex);
        const isComplete = state === 'complete';
        const isCurrent = state === 'current';

        return (
          <li key={step.key} className="flex flex-1 items-center">
            <div
              className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold transition-colors ${
                isComplete
                  ? 'bg-green-600 text-white'
                  : isCurrent
                    ? 'bg-blue-600 text-white ring-4 ring-blue-100 dark:ring-blue-950'
                    : 'bg-gray-200 text-gray-500 dark:bg-gray-800 dark:text-gray-400'
              }`}
              aria-hidden="true"
            >
              {isComplete ? '✓' : index + 1}
            </div>
            <span
              className={`ml-2 text-xs transition-colors ${
                isCurrent ? 'font-semibold text-blue-700 dark:text-blue-300' : isComplete ? 'font-medium text-green-700 dark:text-green-300' : 'text-gray-400 dark:text-gray-500'
              }`}
              aria-current={isCurrent ? 'step' : undefined}
            >
              {step.label}
            </span>
            {index < steps.length - 1 && (
              <div className={`mx-2 h-px flex-1 transition-colors ${isComplete ? 'bg-green-300 dark:bg-green-700' : 'bg-gray-200 dark:bg-gray-800'}`} aria-hidden="true" />
            )}
          </li>
        );
      })}
    </ol>
  );
}
