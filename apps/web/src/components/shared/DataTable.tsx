import { useMemo, useState } from 'react';
import { useIntl } from 'react-intl';

export interface DataTableColumn<TData> {
  key: string;
  header: string;
  accessor: (row: TData) => string | number;
  align?: 'left' | 'right';
  sortable?: boolean;
}

interface DataTableProps<TData> {
  data: TData[];
  columns: DataTableColumn<TData>[];
  getRowKey: (row: TData, index: number) => string;
  caption: string;
  emptyText?: string;
}

type SortDirection = 'asc' | 'desc';

interface SortState {
  key: string;
  direction: SortDirection;
}

function compareValues(left: string | number, right: string | number, direction: SortDirection): number {
  const multiplier = direction === 'asc' ? 1 : -1;
  if (typeof left === 'number' && typeof right === 'number') {
    return (left - right) * multiplier;
  }
  return String(left).localeCompare(String(right)) * multiplier;
}

export function DataTable<TData>({ data, columns, getRowKey, caption, emptyText }: DataTableProps<TData>) {
  const intl = useIntl();
  const [sortState, setSortState] = useState<SortState | null>(null);
  const resolvedEmptyText = emptyText ?? intl.formatMessage({ id: 'dataTable.empty' });

  const sortedData = useMemo(() => {
    if (!sortState) return data;
    const column = columns.find((item) => item.key === sortState.key);
    if (!column) return data;

    return [...data].sort((left, right) => compareValues(column.accessor(left), column.accessor(right), sortState.direction));
  }, [columns, data, sortState]);

  const handleSort = (column: DataTableColumn<TData>): void => {
    if (!column.sortable) return;
    setSortState((current) => {
      if (current?.key !== column.key) {
        return { key: column.key, direction: 'asc' };
      }
      return { key: column.key, direction: current.direction === 'asc' ? 'desc' : 'asc' };
    });
  };

  return (
    <div className="overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
      <div className="overflow-x-auto">
        <table className="w-full min-w-full text-sm">
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr className="border-b bg-gray-50 text-xs text-gray-500 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-300">
              {columns.map((column) => {
                const isSorted = sortState?.key === column.key;
                const sortLabel = isSorted
                  ? intl.formatMessage({ id: sortState.direction === 'asc' ? 'dataTable.sort.asc' : 'dataTable.sort.desc' })
                  : intl.formatMessage({ id: 'dataTable.sort.none' });

                return (
                  <th key={column.key} scope="col" className={`px-4 py-3 font-semibold ${column.align === 'right' ? 'text-right' : 'text-left'}`}>
                    {column.sortable ? (
                      <button
                        type="button"
                        className="inline-flex items-center gap-1 rounded text-inherit focus:outline-none focus:ring-2 focus:ring-blue-500"
                        onClick={() => handleSort(column)}
                        aria-label={intl.formatMessage({ id: 'dataTable.sort.ariaLabel' }, { header: column.header, state: sortLabel })}
                      >
                        {column.header}
                        <span aria-hidden="true">{isSorted ? (sortState.direction === 'asc' ? '↑' : '↓') : '↕'}</span>
                      </button>
                    ) : (
                      column.header
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {sortedData.map((row, index) => (
              <tr key={getRowKey(row, index)} className="border-b dark:border-gray-800 last:border-0">
                {columns.map((column) => (
                  <td key={column.key} className={`px-4 py-3 text-gray-700 dark:text-gray-200 ${column.align === 'right' ? 'text-right' : 'text-left'}`}>
                    {column.accessor(row)}
                  </td>
                ))}
              </tr>
            ))}
            {sortedData.length === 0 && (
              <tr>
                <td colSpan={columns.length} className="px-4 py-8 text-center text-sm text-gray-400 dark:text-gray-500">
                  {resolvedEmptyText}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
