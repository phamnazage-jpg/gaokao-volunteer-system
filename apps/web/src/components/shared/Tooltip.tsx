import { useId, type ReactNode } from 'react';

interface TooltipProps {
  label: string;
  children: ReactNode;
  className?: string;
}

export function Tooltip({ label, children, className = '' }: TooltipProps) {
  const tooltipId = useId();

  return (
    <span className={`group relative inline-flex items-center ${className}`}>
      <span aria-describedby={tooltipId} tabIndex={0} className="inline-flex cursor-help items-center focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded">
        {children}
      </span>
      <span
        id={tooltipId}
        role="tooltip"
        className="pointer-events-none absolute left-1/2 top-full z-20 mt-2 w-56 -translate-x-1/2 rounded-xl bg-gray-900 px-3 py-2 text-left text-xs leading-5 text-white opacity-0 shadow-lg transition-opacity group-focus-within:opacity-100 group-hover:opacity-100"
      >
        {label}
      </span>
    </span>
  );
}
