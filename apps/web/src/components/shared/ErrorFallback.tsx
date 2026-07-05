import type { FallbackProps } from 'react-error-boundary';
import { AlertTriangle, Home, RotateCcw } from 'lucide-react';
import { FormattedMessage, useIntl } from 'react-intl';
import { Link } from 'react-router-dom';

export function ErrorFallback({ resetErrorBoundary }: FallbackProps) {
  const intl = useIntl();
  const safeDetail = intl.formatMessage({ id: 'errorFallback.safeDetail' });

  return (
    <main role="alert" className="flex min-h-full flex-1 items-center justify-center bg-white px-4 py-10 text-center dark:bg-gray-950">
      <section className="w-full max-w-md">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-600 dark:bg-red-950/50 dark:text-red-300">
          <AlertTriangle className="h-6 w-6" aria-hidden="true" />
        </div>
        <h1 className="mt-4 text-xl font-semibold text-gray-900 dark:text-gray-100">
          <FormattedMessage id="errorFallback.title" />
        </h1>
        <p className="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
          <FormattedMessage id="errorFallback.description" />
        </p>
        <p className="mt-3 rounded bg-gray-50 px-3 py-2 text-xs text-gray-500 dark:bg-gray-900 dark:text-gray-400">{safeDetail}</p>
        <div className="mt-6 flex flex-col justify-center gap-2 sm:flex-row">
          <button
            type="button"
            onClick={resetErrorBoundary}
            className="inline-flex h-10 items-center justify-center gap-2 rounded bg-gray-100 px-4 text-sm font-medium text-gray-700 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-300 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
          >
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
            <FormattedMessage id="errorFallback.retry" />
          </button>
          <Link
            to="/"
            className="inline-flex h-10 items-center justify-center gap-2 rounded bg-blue-600 px-4 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            <Home className="h-4 w-4" aria-hidden="true" />
            <FormattedMessage id="errorFallback.backHome" />
          </Link>
        </div>
      </section>
    </main>
  );
}
