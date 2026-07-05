import { AlertTriangle, Home, RotateCcw } from 'lucide-react';
import { FormattedMessage } from 'react-intl';
import { Link, useNavigate } from 'react-router-dom';

interface AdminErrorPageProps {
  onRetry?: () => void;
}

export function AdminErrorPage({ onRetry }: AdminErrorPageProps) {
  const navigate = useNavigate();
  const handleRetry = (): void => {
    if (onRetry) {
      onRetry();
      return;
    }

    void navigate(0);
  };

  return (
    <main className="min-h-[calc(100vh-6rem)] bg-slate-50 px-4 py-8 text-slate-950 dark:bg-slate-950 dark:text-slate-100">
      <section
        aria-labelledby="admin-error-title"
        className="mx-auto flex max-w-3xl flex-col items-center rounded-[2rem] border border-red-100 bg-white p-8 text-center shadow-xl dark:border-red-950/60 dark:bg-slate-900"
      >
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-300">
          <AlertTriangle className="h-7 w-7" aria-hidden="true" />
        </div>
        <p className="mt-5 text-sm font-semibold uppercase tracking-[0.32em] text-red-600 dark:text-red-300">
          <FormattedMessage id="admin.error.eyebrow" />
        </p>
        <h1 id="admin-error-title" className="mt-3 text-2xl font-black sm:text-3xl">
          <FormattedMessage id="admin.error.title" />
        </h1>
        <p className="mt-4 max-w-xl text-sm leading-6 text-slate-500 dark:text-slate-400">
          <FormattedMessage id="admin.error.description" />
        </p>

        <div className="mt-6 grid w-full max-w-2xl gap-3 text-left sm:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
              <FormattedMessage id="admin.error.suggestionOneLabel" />
            </p>
            <p className="mt-2 text-sm font-semibold">
              <FormattedMessage id="admin.error.suggestionOne" />
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
              <FormattedMessage id="admin.error.suggestionTwoLabel" />
            </p>
            <p className="mt-2 text-sm font-semibold">
              <FormattedMessage id="admin.error.suggestionTwo" />
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
              <FormattedMessage id="admin.error.suggestionThreeLabel" />
            </p>
            <p className="mt-2 text-sm font-semibold">
              <FormattedMessage id="admin.error.suggestionThree" />
            </p>
          </div>
        </div>

        <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
          <button
            type="button"
            onClick={handleRetry}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-400 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
          >
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
            <FormattedMessage id="admin.error.retry" />
          </button>
          <Link
            to="/admin"
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 text-sm font-semibold text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            <Home className="h-4 w-4" aria-hidden="true" />
            <FormattedMessage id="admin.error.backToDashboard" />
          </Link>
        </div>
      </section>
    </main>
  );
}
