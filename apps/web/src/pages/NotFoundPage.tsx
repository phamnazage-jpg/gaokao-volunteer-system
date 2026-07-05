import { Link } from 'react-router-dom';
import { FormattedMessage } from 'react-intl';

export function NotFoundPage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-4 text-center">
      <div className="text-5xl" aria-hidden="true">🧭</div>
      <h1 className="mt-4 text-xl font-bold text-gray-900 dark:text-gray-100">
        <FormattedMessage id="notFound.title" />
      </h1>
      <p className="mt-2 max-w-sm text-sm text-gray-500 dark:text-gray-400">
        <FormattedMessage id="notFound.description" />
      </p>
      <Link to="/" className="mt-6 rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
        <FormattedMessage id="notFound.backHome" />
      </Link>
    </main>
  );
}
