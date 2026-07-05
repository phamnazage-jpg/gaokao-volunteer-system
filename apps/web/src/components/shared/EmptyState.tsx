import { Link } from 'react-router-dom';

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
}

export function EmptyState({ title, description, actionLabel, actionHref }: EmptyStateProps) {
  return (
    <section
      className="rounded-3xl border border-dashed border-blue-200 bg-gradient-to-br from-blue-50 via-white to-cyan-50 px-6 py-10 text-center shadow-sm dark:border-blue-900/60 dark:from-blue-950/30 dark:via-gray-900 dark:to-cyan-950/30"
      aria-live="polite"
    >
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-100 text-lg dark:bg-blue-950/60 dark:text-blue-200" aria-hidden="true">
        ✦
      </div>
      <h2 className="mt-4 text-base font-semibold text-gray-900 dark:text-gray-100">{title}</h2>
      <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-gray-600 dark:text-gray-300">{description}</p>
      {actionLabel && actionHref && (
        <Link
          to={actionHref}
          className="mt-5 inline-flex min-h-[44px] items-center justify-center rounded-full bg-blue-600 px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
        >
          {actionLabel}
        </Link>
      )}
    </section>
  );
}
