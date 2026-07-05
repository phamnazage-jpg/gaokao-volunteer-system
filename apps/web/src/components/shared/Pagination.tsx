import { useIntl } from 'react-intl';

interface PaginationProps {
  page: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  label?: string;
}

function clampPage(page: number, totalPages: number): number {
  return Math.min(Math.max(page, 1), totalPages);
}

export function Pagination({ page, pageSize, totalItems, onPageChange, label }: PaginationProps) {
  const intl = useIntl();
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const safePage = clampPage(page, totalPages);
  const start = totalItems === 0 ? 0 : (safePage - 1) * pageSize + 1;
  const end = Math.min(safePage * pageSize, totalItems);

  if (totalItems <= pageSize) {
    return null;
  }

  return (
    <nav className="mt-5 flex flex-col gap-3 rounded-2xl border border-gray-100 bg-white p-3 text-sm shadow-sm dark:border-gray-800 dark:bg-gray-900 sm:flex-row sm:items-center sm:justify-between" aria-label={label ?? intl.formatMessage({ id: 'pagination.ariaLabel' })}>
      <p className="text-xs text-gray-500 dark:text-gray-400" aria-live="polite">
        {intl.formatMessage({ id: 'pagination.range' }, { start, end, total: totalItems })}
      </p>
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="min-h-[40px] rounded-full border border-gray-200 px-4 font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
          disabled={safePage === 1}
          onClick={() => onPageChange(clampPage(safePage - 1, totalPages))}
        >
          {intl.formatMessage({ id: 'pagination.previous' })}
        </button>
        <span className="min-w-16 text-center text-xs font-semibold text-gray-500 dark:text-gray-400">
          {safePage} / {totalPages}
        </span>
        <button
          type="button"
          className="min-h-[40px] rounded-full border border-gray-200 px-4 font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
          disabled={safePage === totalPages}
          onClick={() => onPageChange(clampPage(safePage + 1, totalPages))}
        >
          {intl.formatMessage({ id: 'pagination.next' })}
        </button>
      </div>
    </nav>
  );
}
