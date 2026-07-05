import { useState } from 'react';
import { Database } from 'lucide-react';
import { FormattedMessage, useIntl } from 'react-intl';
import { useScoreLineQuery, useRankEstimatorQuery, useMajorsQuery, useSchoolsQuery } from '@/hooks/useDataQuery';
import { Modal } from '@/components/shared/Modal';
import { toast } from '@/components/shared/Toast';
import { DataQueryForm, type DataQueryFormValues, type ScoreType } from '@/components/DataQueryForm';
import { DataQueryResult } from '@/components/DataQueryResult';

export function DataQueryPage() {
  const intl = useIntl();
  const [formValues, setFormValues] = useState<DataQueryFormValues>({
    province: intl.formatMessage({ id: 'dataQuery.defaultProvince' }),
    year: 2025,
    scoreType: 'physics',
    rank: 12500,
    keyword: '',
  });
  const [showMethodology, setShowMethodology] = useState(false);

  const scoreLine = useScoreLineQuery({
    province: formValues.province,
    year: formValues.year,
    scoreType: formValues.scoreType,
  });
  const rankEst = useRankEstimatorQuery({
    province: formValues.province,
    year: formValues.year,
    scoreType: formValues.scoreType,
    rank: formValues.rank,
  });
  const majors = useMajorsQuery(formValues.keyword);
  const schools = useSchoolsQuery(formValues.keyword);

  const handleFormChange = (patch: Partial<DataQueryFormValues>): void => {
    setFormValues((current) => ({ ...current, ...patch }));
  };

  const handleScoreTypeChange = (nextScoreType: ScoreType): void => {
    toast.info(intl.formatMessage({ id: 'dataQuery.toast.scoreTypeChanged.title' }), {
      description: intl.formatMessage(
        { id: 'dataQuery.toast.scoreTypeChanged.description' },
        { scoreType: intl.formatMessage({ id: nextScoreType === 'physics' ? 'dataQuery.scoreType.physics' : 'dataQuery.scoreType.history' }) },
      ),
    });
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2 dark:text-gray-100">
          <Database className="w-6 h-6" aria-hidden="true" />
          <FormattedMessage id="dataQuery.page.title" />
        </h1>
        <button
          type="button"
          className="inline-flex min-h-[40px] items-center justify-center rounded-full border border-blue-200 bg-blue-50 px-4 text-sm font-semibold text-blue-700 transition hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:border-blue-500/30 dark:bg-blue-500/10 dark:text-blue-200 dark:hover:bg-blue-500/20 dark:focus:ring-offset-gray-950"
          onClick={() => setShowMethodology(true)}
        >
          <FormattedMessage id="dataQuery.page.methodologyAction" />
        </button>
      </div>

      <Modal
        open={showMethodology}
        title={intl.formatMessage({ id: 'dataQuery.methodology.title' })}
        description={intl.formatMessage({ id: 'dataQuery.methodology.description' })}
        closeLabel={intl.formatMessage({ id: 'dataQuery.methodology.close' })}
        onClose={() => setShowMethodology(false)}
      >
        <ul className="space-y-3">
          <li>
            <strong className="text-gray-900 dark:text-gray-100">
              <FormattedMessage id="dataQuery.methodology.scoreLine.label" />
            </strong>
            <FormattedMessage id="dataQuery.methodology.scoreLine.description" />
          </li>
          <li>
            <strong className="text-gray-900 dark:text-gray-100">
              <FormattedMessage id="dataQuery.methodology.rank.label" />
            </strong>
            <FormattedMessage id="dataQuery.methodology.rank.description" />
          </li>
          <li>
            <strong className="text-gray-900 dark:text-gray-100">
              <FormattedMessage id="dataQuery.methodology.search.label" />
            </strong>
            <FormattedMessage id="dataQuery.methodology.search.description" />
          </li>
        </ul>
      </Modal>

      <div className="mt-6 grid gap-4">
        <DataQueryForm variant="scoreLine" values={formValues} onChange={handleFormChange} onScoreTypeChange={handleScoreTypeChange} />
        <DataQueryForm variant="rankEstimator" values={formValues} onChange={handleFormChange} onScoreTypeChange={handleScoreTypeChange} />
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <DataQueryForm variant="majors" values={formValues} onChange={handleFormChange} />
        <DataQueryForm variant="schools" values={formValues} onChange={handleFormChange} />
      </div>

      <DataQueryResult
        scoreLine={scoreLine.data}
        rankEstimator={rankEst.data}
        majors={majors.data}
        schools={schools.data}
        loading={{
          scoreLine: scoreLine.isLoading,
          rankEstimator: rankEst.isLoading,
          majors: majors.isLoading,
          schools: schools.isLoading,
        }}
        error={{
          scoreLine: scoreLine.isError,
          rankEstimator: rankEst.isError,
          majors: majors.isError,
          schools: schools.isError,
        }}
      />
    </div>
  );
}
