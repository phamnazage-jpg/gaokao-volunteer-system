import { GraduationCap, TrendingUp } from 'lucide-react';
import { useIntl } from 'react-intl';
import { BarMetricChart } from '@/components/shared/Charts';
import { DataTable, type DataTableColumn } from '@/components/shared/DataTable';
import type { MajorsResponse, RankEstimatorResponse, SchoolsResponse, ScoreLineResponse } from '@/hooks/useDataQuery';

type ScoreLineRow = ScoreLineResponse['lines'][number];
type MajorRow = MajorsResponse['majors'][number];
type SchoolRow = SchoolsResponse['schools'][number];

interface DataQueryResultProps {
  scoreLine?: ScoreLineResponse;
  rankEstimator?: RankEstimatorResponse;
  majors?: MajorsResponse;
  schools?: SchoolsResponse;
  loading?: Partial<Record<'scoreLine' | 'rankEstimator' | 'majors' | 'schools', boolean>>;
  error?: Partial<Record<'scoreLine' | 'rankEstimator' | 'majors' | 'schools', boolean>>;
}

function QueryStatusCard({ state, label }: { state: 'loading' | 'error' | 'empty'; label: string }) {
  const intl = useIntl();
  let messageKey = 'dataQuery.result.status.empty';
  let toneClass = 'border-gray-100 bg-white text-gray-500 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-400';

  if (state === 'loading') {
    messageKey = 'dataQuery.result.status.loading';
  }

  if (state === 'error') {
    messageKey = 'dataQuery.result.status.error';
    toneClass = 'border-red-200 bg-red-50 text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200';
  }

  return (
    <div role={state === 'error' ? 'alert' : 'status'} className={`rounded-xl border p-4 text-sm shadow-sm ${toneClass}`}>
      {intl.formatMessage({ id: messageKey }, { label })}
    </div>
  );
}

export function DataQueryResult({ scoreLine, rankEstimator, majors, schools, loading = {}, error = {} }: DataQueryResultProps) {
  const intl = useIntl();
  const resultLabels = {
    scoreLine: intl.formatMessage({ id: 'dataQuery.result.scoreLine.titleShort' }),
    rankEstimator: intl.formatMessage({ id: 'dataQuery.result.rank.titleShort' }),
    majors: intl.formatMessage({ id: 'dataQuery.result.majors.title' }),
    schools: intl.formatMessage({ id: 'dataQuery.result.schools.title' }),
  };
  const scoreLineColumns: DataTableColumn<ScoreLineRow>[] = [
    { key: 'batch', header: intl.formatMessage({ id: 'dataQuery.result.columns.batch' }), accessor: (line) => line.batch, sortable: true },
    { key: 'score', header: intl.formatMessage({ id: 'dataQuery.result.columns.score' }), accessor: (line) => line.score, align: 'right', sortable: true },
    { key: 'rank', header: intl.formatMessage({ id: 'dataQuery.result.columns.rank' }), accessor: (line) => line.rank.toLocaleString(), align: 'right' },
  ];
  const majorColumns: DataTableColumn<MajorRow>[] = [
    { key: 'name', header: intl.formatMessage({ id: 'dataQuery.result.columns.major' }), accessor: (major) => major.name, sortable: true },
    { key: 'category', header: intl.formatMessage({ id: 'dataQuery.result.columns.category' }), accessor: (major) => major.category, sortable: true },
  ];
  const schoolColumns: DataTableColumn<SchoolRow>[] = [
    { key: 'name', header: intl.formatMessage({ id: 'dataQuery.result.columns.school' }), accessor: (school) => school.name, sortable: true },
    { key: 'province', header: intl.formatMessage({ id: 'dataQuery.result.columns.province' }), accessor: (school) => school.province, sortable: true },
    {
      key: 'tags',
      header: intl.formatMessage({ id: 'dataQuery.result.columns.tags' }),
      accessor: (school) => [school.is985 ? '985' : '', school.is211 ? '211' : ''].filter(Boolean).join(' / ') || intl.formatMessage({ id: 'dataQuery.result.tags.regularUndergraduate' }),
    },
  ];

  return (
    <div className="mt-6 grid gap-4">
      <section className="rounded-2xl border border-blue-100 bg-blue-50/70 p-4 text-sm text-blue-900 dark:border-blue-500/20 dark:bg-blue-500/10 dark:text-blue-100">
        <h2 className="font-semibold">{intl.formatMessage({ id: 'dataQuery.result.overviewTitle' })}</h2>
        <p className="mt-1 leading-6 text-blue-800/80 dark:text-blue-100/80">{intl.formatMessage({ id: 'dataQuery.result.overviewDescription' })}</p>
      </section>

      {error.rankEstimator && <QueryStatusCard state="error" label={resultLabels.rankEstimator} />}
      {loading.rankEstimator && <QueryStatusCard state="loading" label={resultLabels.rankEstimator} />}
      {!loading.rankEstimator && !error.rankEstimator && !rankEstimator && <QueryStatusCard state="empty" label={resultLabels.rankEstimator} />}
      {rankEstimator && !error.rankEstimator && (
        <section className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900" aria-label={intl.formatMessage({ id: 'dataQuery.result.rank.ariaLabel' })}>
          <div className="flex items-center gap-3">
            <TrendingUp className="h-8 w-8 text-blue-500" aria-hidden="true" />
            <div>
              <p className="text-xs text-gray-400 dark:text-gray-500">{intl.formatMessage({ id: 'dataQuery.result.rank.equivalentScore' })}</p>
              <p className="text-2xl font-bold text-gray-800 dark:text-gray-100">{rankEstimator.equivalentScore}</p>
            </div>
          </div>
        </section>
      )}

      {error.scoreLine && <QueryStatusCard state="error" label={resultLabels.scoreLine} />}
      {loading.scoreLine && <QueryStatusCard state="loading" label={resultLabels.scoreLine} />}
      {!loading.scoreLine && !error.scoreLine && !scoreLine && <QueryStatusCard state="empty" label={resultLabels.scoreLine} />}
      {scoreLine && !error.scoreLine && (
        <section className="grid gap-4" aria-label={intl.formatMessage({ id: 'dataQuery.result.scoreLine.ariaLabel' })}>
          <div>
            <p className="mb-2 text-xs font-semibold text-gray-400 dark:text-gray-500">
              {intl.formatMessage({ id: 'dataQuery.result.scoreLine.title' }, { year: scoreLine.year })}
            </p>
            <DataTable
              data={scoreLine.lines}
              columns={scoreLineColumns}
              getRowKey={(line) => line.batch}
              caption={intl.formatMessage({ id: 'dataQuery.result.scoreLine.caption' }, { year: scoreLine.year })}
              emptyText={intl.formatMessage({ id: 'dataQuery.result.emptyTable' })}
            />
          </div>
          <BarMetricChart
            title={intl.formatMessage({ id: 'dataQuery.result.scoreLine.chartTitle' })}
            ariaLabel={intl.formatMessage({ id: 'dataQuery.result.scoreLine.chartAriaLabel' })}
            data={scoreLine.lines.map((line) => ({ label: line.batch, value: line.score }))}
            emptyText={intl.formatMessage({ id: 'dataQuery.result.emptyChart' })}
          />
        </section>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {error.majors && <QueryStatusCard state="error" label={resultLabels.majors} />}
        {loading.majors && <QueryStatusCard state="loading" label={resultLabels.majors} />}
        {!loading.majors && !error.majors && !majors && <QueryStatusCard state="empty" label={resultLabels.majors} />}
        {majors && !error.majors && (
          <section className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900" aria-label={intl.formatMessage({ id: 'dataQuery.result.majors.ariaLabel' })}>
            <p className="mb-2 flex items-center gap-1 text-xs font-semibold text-gray-400 dark:text-gray-500">
              <GraduationCap className="h-4 w-4" aria-hidden="true" /> {intl.formatMessage({ id: 'dataQuery.result.majors.title' })}
            </p>
            <DataTable
              data={majors.majors.slice(0, 8)}
              columns={majorColumns}
              getRowKey={(major) => major.id}
              caption={intl.formatMessage({ id: 'dataQuery.result.majors.caption' }, { total: majors.total })}
              emptyText={intl.formatMessage({ id: 'dataQuery.result.emptyTable' })}
            />
          </section>
        )}

        {error.schools && <QueryStatusCard state="error" label={resultLabels.schools} />}
        {loading.schools && <QueryStatusCard state="loading" label={resultLabels.schools} />}
        {!loading.schools && !error.schools && !schools && <QueryStatusCard state="empty" label={resultLabels.schools} />}
        {schools && !error.schools && (
          <section className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900" aria-label={intl.formatMessage({ id: 'dataQuery.result.schools.ariaLabel' })}>
            <p className="mb-2 text-xs font-semibold text-gray-400 dark:text-gray-500">{intl.formatMessage({ id: 'dataQuery.result.schools.title' })}</p>
            <DataTable
              data={schools.schools.slice(0, 8)}
              columns={schoolColumns}
              getRowKey={(school) => school.id}
              caption={intl.formatMessage({ id: 'dataQuery.result.schools.caption' }, { total: schools.total })}
              emptyText={intl.formatMessage({ id: 'dataQuery.result.emptyTable' })}
            />
          </section>
        )}
      </div>
    </div>
  );
}
