import { FormattedMessage, useIntl } from 'react-intl';

export function RouteFallback() {
  const intl = useIntl();

  return (
    <div
      role="status"
      aria-label={intl.formatMessage({ id: 'routeFallback.ariaLabel' })}
      className="flex items-center justify-center min-h-[48px] py-12 text-sm text-gray-500 dark:text-gray-400"
    >
      <div className="flex flex-col items-center gap-3">
        <div className="flex gap-1.5" aria-hidden="true">
          <div className="w-2 h-2 bg-gray-300 rounded-full animate-pulse dark:bg-gray-600" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 bg-gray-300 rounded-full animate-pulse dark:bg-gray-600" style={{ animationDelay: '120ms' }} />
          <div className="w-2 h-2 bg-gray-300 rounded-full animate-pulse dark:bg-gray-600" style={{ animationDelay: '240ms' }} />
        </div>
        <span>
          <FormattedMessage id="routeFallback.label" />
        </span>
      </div>
    </div>
  );
}
