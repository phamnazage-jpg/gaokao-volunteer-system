import { useState } from 'react';
import { useIntl } from 'react-intl';
import { DataTable, type DataTableColumn } from '@/components/shared/DataTable';
import { Modal } from '@/components/shared/Modal';
import { useMajorsQuery, type MajorsResponse } from '@/hooks/useDataQuery';

type MajorRow = MajorsResponse['majors'][number];

export function AdminMajorsPage() {
  const intl = useIntl();
  const [keyword, setKeyword] = useState('');
  const [selectedMajor, setSelectedMajor] = useState<MajorRow | null>(null);
  const majorsQuery = useMajorsQuery(keyword);
  const majors = majorsQuery.data?.majors ?? [];
  const total = majorsQuery.data?.total ?? majors.length;
  const columns: DataTableColumn<MajorRow>[] = [
    { key: 'name', header: intl.formatMessage({ id: 'admin.majors.columns.name' }), accessor: (row) => row.name, sortable: true },
    { key: 'category', header: intl.formatMessage({ id: 'admin.majors.columns.category' }), accessor: (row) => row.category, sortable: true },
    { key: 'id', header: intl.formatMessage({ id: 'admin.majors.columns.id' }), accessor: (row) => row.id, sortable: true },
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold text-blue-600 dark:text-blue-300">T-E-15</p>
            <h2 className="mt-1 text-2xl font-black text-slate-950 dark:text-white">{intl.formatMessage({ id: 'admin.majors.title' })}</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
              {intl.formatMessage({ id: 'admin.majors.description' })}
            </p>
          </div>
          <label className="flex min-w-full flex-col gap-1 lg:min-w-[22rem]">
            <span className="text-xs text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.majors.searchLabel' })}</span>
            <input
              type="search"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder={intl.formatMessage({ id: 'admin.majors.searchPlaceholder' })}
              className="min-h-12 rounded-xl border border-slate-200 px-3 text-sm text-slate-800 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            />
          </label>
        </div>
      </section>

      {majorsQuery.isLoading && (
        <div role="status" className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
          {intl.formatMessage({ id: 'admin.majors.loading' })}
        </div>
      )}

      {majorsQuery.isError && (
        <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
          {intl.formatMessage({ id: 'admin.majors.error' })}
        </div>
      )}

      {!majorsQuery.isLoading && !majorsQuery.isError && (
        <section aria-label={intl.formatMessage({ id: 'admin.majors.tableAriaLabel' })}>
          <div className="mb-3 flex items-center justify-between text-sm">
            <h3 className="font-bold text-slate-950 dark:text-white">{intl.formatMessage({ id: 'admin.majors.resultTitle' })}</h3>
            <span className="text-slate-500 dark:text-slate-400">{intl.formatMessage({ id: 'admin.majors.total' }, { total })}</span>
          </div>
          <DataTable
            data={majors}
            columns={columns}
            getRowKey={(row) => row.id}
            caption={intl.formatMessage({ id: 'admin.majors.tableCaption' }, { total })}
            emptyText={intl.formatMessage({ id: 'admin.majors.empty' })}
          />
          {majors.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {majors.map((major) => (
                <button
                  key={major.id}
                  type="button"
                  onClick={() => setSelectedMajor(major)}
                  className="inline-flex min-h-9 items-center rounded-full border border-blue-200 bg-blue-50 px-3 text-xs font-semibold text-blue-700 transition hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-blue-500/30 dark:bg-blue-500/10 dark:text-blue-200"
                >
                  {intl.formatMessage({ id: 'admin.majors.viewDetail' }, { name: major.name })}
                </button>
              ))}
            </div>
          )}
        </section>
      )}

      <Modal
        open={selectedMajor !== null}
        title={selectedMajor?.name ?? intl.formatMessage({ id: 'admin.majors.detailTitleFallback' })}
        description={selectedMajor ? intl.formatMessage({ id: 'admin.majors.detailDescription' }, { category: selectedMajor.category }) : undefined}
        onClose={() => setSelectedMajor(null)}
      >
        {selectedMajor && (
          <dl className="space-y-3">
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">{intl.formatMessage({ id: 'admin.majors.columns.id' })}</dt>
              <dd className="font-semibold text-slate-950">{selectedMajor.id}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">{intl.formatMessage({ id: 'admin.majors.columns.category' })}</dt>
              <dd className="font-semibold text-slate-950">{selectedMajor.category}</dd>
            </div>
            <p className="rounded-2xl bg-slate-50 p-4 text-sm leading-6 text-slate-600">
              {intl.formatMessage({ id: 'admin.majors.detailNote' })}
            </p>
          </dl>
        )}
      </Modal>
    </div>
  );
}
