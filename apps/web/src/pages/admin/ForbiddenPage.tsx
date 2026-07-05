import { Link } from 'react-router-dom';
import { FormattedMessage } from 'react-intl';

export function ForbiddenPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 text-center text-slate-950 dark:bg-slate-950 dark:text-slate-100">
      <section className="max-w-md rounded-[2rem] border border-slate-200 bg-white p-8 shadow-xl dark:border-slate-800 dark:bg-slate-900">
        <p className="text-sm font-semibold text-red-600 dark:text-red-300">403</p>
        <h1 className="mt-3 text-2xl font-black">
          <FormattedMessage id="admin.forbidden.title" />
        </h1>
        <p className="mt-3 text-sm leading-6 text-slate-500 dark:text-slate-400">
          <FormattedMessage id="admin.forbidden.description" />
        </p>
        <Link to="/admin/login" className="mt-6 inline-flex min-h-10 items-center rounded-xl bg-blue-600 px-4 text-sm font-medium text-white hover:bg-blue-700">
          <FormattedMessage id="admin.forbidden.backToLogin" />
        </Link>
      </section>
    </main>
  );
}
