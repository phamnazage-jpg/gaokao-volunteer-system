import { useState } from 'react';
import { useIntl } from 'react-intl';
import { DataQueryForm, type DataQueryFormValues } from '@/components/DataQueryForm';
import { DataQueryResult } from '@/components/DataQueryResult';
import { useScoreLineQuery } from '@/hooks/useDataQuery';

export function AdminScoreLinesPage() {
  const intl = useIntl();
  const [values, setValues] = useState<DataQueryFormValues>({
    province: intl.formatMessage({ id: 'dataQuery.defaultProvince' }),
    year: 2025,
    scoreType: 'physics',
    rank: 12500,
    keyword: '',
  });
  const scoreLine = useScoreLineQuery({
    province: values.province,
    year: values.year,
    scoreType: values.scoreType,
  });

  const handleChange = (patch: Partial<DataQueryFormValues>): void => {
    setValues((current) => ({ ...current, ...patch }));
  };

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div>
          <p className="text-sm font-semibold text-blue-600 dark:text-blue-300">T-E-13</p>
          <h2 className="mt-1 text-2xl font-black text-slate-950 dark:text-white">{intl.formatMessage({ id: 'admin.scoreLines.title' })}</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
            {intl.formatMessage({ id: 'admin.scoreLines.description' })}
          </p>
        </div>
      </section>

      <DataQueryForm variant="scoreLine" values={values} onChange={handleChange} />

      {scoreLine.isLoading && (
        <div role="status" className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
          {intl.formatMessage({ id: 'admin.scoreLines.loading' })}
        </div>
      )}

      {scoreLine.isError && (
        <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
          {intl.formatMessage({ id: 'admin.scoreLines.error' })}
        </div>
      )}

      {!scoreLine.isLoading && !scoreLine.isError && <DataQueryResult scoreLine={scoreLine.data} />}
    </div>
  );
}
