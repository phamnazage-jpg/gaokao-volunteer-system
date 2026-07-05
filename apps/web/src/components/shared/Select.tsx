import { useId } from 'react';

export interface SelectOption<TValue extends string = string> {
  value: TValue;
  label: string;
}

interface SelectProps<TValue extends string = string> {
  label: string;
  value: TValue;
  options: SelectOption<TValue>[];
  onChange: (value: TValue) => void;
  helpText?: string;
  className?: string;
}

export function Select<TValue extends string = string>({ label, value, options, onChange, helpText, className = '' }: SelectProps<TValue>) {
  const selectId = useId();
  const helpId = useId();

  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      <label className="text-xs text-gray-500 dark:text-gray-400" htmlFor={selectId}>
        {label}
      </label>
      <select
        id={selectId}
        value={value}
        aria-describedby={helpText ? helpId : undefined}
        onChange={(event) => onChange(event.target.value as TValue)}
        className="min-h-[48px] rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {helpText && (
        <span id={helpId} className="text-xs leading-5 text-gray-400 dark:text-gray-500">
          {helpText}
        </span>
      )}
    </div>
  );
}
