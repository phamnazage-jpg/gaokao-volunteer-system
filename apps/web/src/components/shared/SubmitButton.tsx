import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { LoaderCircle } from 'lucide-react';
import { clsx } from 'clsx';

interface SubmitButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'type' | 'children'> {
  isSubmitting: boolean;
  idleLabel: ReactNode;
  submittingLabel?: ReactNode;
}

export function SubmitButton({
  isSubmitting,
  idleLabel,
  submittingLabel = '提交中...',
  disabled,
  className,
  ...props
}: SubmitButtonProps) {
  return (
    <button
      {...props}
      type="submit"
      disabled={disabled === true || isSubmitting}
      aria-busy={isSubmitting}
      className={clsx(
        'inline-flex h-10 items-center justify-center gap-2 rounded px-4 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
    >
      {isSubmitting && <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />}
      {isSubmitting ? submittingLabel : idleLabel}
    </button>
  );
}
