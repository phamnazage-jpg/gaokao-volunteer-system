import { useId } from 'react';

interface DatePickerProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  helpText?: string;
  className?: string;
}

export function DatePicker({ label, value, onChange, helpText, className = '' }: DatePickerProps) {
  const inputId = useId();
  const helpId = useId();

  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      <label htmlFor={inputId} className="text-xs text-gray-500 dark:text-gray-400">
        {label}
      </label>
      <input
        id={inputId}
        type="date"
        value={value}
        aria-describedby={helpText ? helpId : undefined}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-[44px] rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:[color-scheme:dark]"
      />
      {helpText && (
        <span id={helpId} className="text-xs leading-5 text-gray-400 dark:text-gray-500">
          {helpText}
        </span>
      )}
    </div>
  );
}
