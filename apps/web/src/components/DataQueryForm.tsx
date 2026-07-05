import { Search } from 'lucide-react';
import { useIntl } from 'react-intl';
import { Select, type SelectOption } from '@/components/shared/Select';
import { Tooltip } from '@/components/shared/Tooltip';

export type ScoreType = 'physics' | 'history';
export type DataQueryFormVariant = 'scoreLine' | 'rankEstimator' | 'majors' | 'schools';

export interface DataQueryFormValues {
  province: string;
  year: number;
  scoreType: ScoreType;
  rank: number;
  keyword: string;
}

interface DataQueryFormProps {
  variant: DataQueryFormVariant;
  values: DataQueryFormValues;
  onChange: (patch: Partial<DataQueryFormValues>) => void;
  onScoreTypeChange?: (scoreType: ScoreType) => void;
}

const SCORE_TYPE_OPTION_KEYS: ReadonlyArray<{ value: ScoreType; labelKey: string }> = [
  { value: 'physics', labelKey: 'dataQuery.scoreType.physics' },
  { value: 'history', labelKey: 'dataQuery.scoreType.history' },
];

const VARIANT_META: Record<DataQueryFormVariant, { titleKey: string; descriptionKey: string; keywordPlaceholderKey?: string }> = {
  scoreLine: {
    titleKey: 'dataQuery.form.scoreLine.title',
    descriptionKey: 'dataQuery.form.scoreLine.description',
  },
  rankEstimator: {
    titleKey: 'dataQuery.form.rankEstimator.title',
    descriptionKey: 'dataQuery.form.rankEstimator.description',
  },
  majors: {
    titleKey: 'dataQuery.form.majors.title',
    descriptionKey: 'dataQuery.form.majors.description',
    keywordPlaceholderKey: 'dataQuery.form.majors.keywordPlaceholder',
  },
  schools: {
    titleKey: 'dataQuery.form.schools.title',
    descriptionKey: 'dataQuery.form.schools.description',
    keywordPlaceholderKey: 'dataQuery.form.schools.keywordPlaceholder',
  },
};

export function DataQueryForm({ variant, values, onChange, onScoreTypeChange }: DataQueryFormProps) {
  const intl = useIntl();
  const meta = VARIANT_META[variant];
  const title = intl.formatMessage({ id: meta.titleKey });
  const description = intl.formatMessage({ id: meta.descriptionKey });
  const provinceLabel = intl.formatMessage({ id: 'dataQuery.form.province.label' });
  const yearLabel = intl.formatMessage({ id: 'dataQuery.form.year.label' });
  const keywordLabel = intl.formatMessage({ id: 'dataQuery.form.keyword.label' });
  const scoreTypeOptions: SelectOption<ScoreType>[] = SCORE_TYPE_OPTION_KEYS.map((option) => ({
    value: option.value,
    label: intl.formatMessage({ id: option.labelKey }),
  }));
  const showProvince = variant === 'scoreLine' || variant === 'rankEstimator' || variant === 'schools';
  const showYear = variant === 'scoreLine' || variant === 'rankEstimator';
  const showScoreType = variant === 'scoreLine' || variant === 'rankEstimator';
  const showRank = variant === 'rankEstimator';
  const showKeyword = variant === 'majors' || variant === 'schools';

  const handleScoreTypeChange = (scoreType: ScoreType): void => {
    onChange({ scoreType });
    onScoreTypeChange?.(scoreType);
  };

  return (
    <section className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900" aria-label={title}>
      <div className="mb-4 flex flex-col gap-1">
        <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">{title}</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        {showProvince && (
          <label className="flex flex-col gap-1">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {provinceLabel}
              <Tooltip label={intl.formatMessage({ id: 'dataQuery.form.province.tooltip' })} className="ml-1">
                <span className="text-gray-400 dark:text-gray-500" aria-label={intl.formatMessage({ id: 'dataQuery.form.province.tooltipAria' })}>
                  ?
                </span>
              </Tooltip>
            </span>
            <input
              type="text"
              aria-label={intl.formatMessage({ id: 'dataQuery.form.fieldAria' }, { title, field: provinceLabel })}
              value={values.province}
              onChange={(event) => onChange({ province: event.target.value })}
              className="min-h-[48px] rounded-lg border border-gray-200 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
            />
          </label>
        )}

        {showYear && (
          <label className="flex flex-col gap-1">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {yearLabel}
              <Tooltip label={intl.formatMessage({ id: 'dataQuery.form.year.tooltip' })} className="ml-1">
                <span className="text-gray-400 dark:text-gray-500" aria-label={intl.formatMessage({ id: 'dataQuery.form.year.tooltipAria' })}>
                  ?
                </span>
              </Tooltip>
            </span>
            <input
              type="number"
              aria-label={intl.formatMessage({ id: 'dataQuery.form.fieldAria' }, { title, field: yearLabel })}
              value={values.year}
              onChange={(event) => onChange({ year: Number(event.target.value) })}
              className="min-h-[48px] rounded-lg border border-gray-200 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
            />
          </label>
        )}

        {showScoreType && (
          <div className="flex flex-col gap-1">
            <div className="text-xs text-gray-500 dark:text-gray-400">
              {intl.formatMessage({ id: 'dataQuery.form.scoreType.label' })}
              <Tooltip label={intl.formatMessage({ id: 'dataQuery.form.scoreType.tooltip' })} className="ml-1">
                <span className="text-gray-400 dark:text-gray-500" aria-label={intl.formatMessage({ id: 'dataQuery.form.scoreType.tooltipAria' })}>
                  ?
                </span>
              </Tooltip>
            </div>
            <Select
              label={intl.formatMessage({ id: 'dataQuery.form.scoreType.selectLabel' })}
              value={values.scoreType}
              options={scoreTypeOptions}
              onChange={handleScoreTypeChange}
              helpText={intl.formatMessage({ id: 'dataQuery.form.scoreType.help' })}
            />
          </div>
        )}

        {showRank && (
          <label className="flex flex-col gap-1">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {intl.formatMessage({ id: 'dataQuery.form.rank.label' })}
              <Tooltip label={intl.formatMessage({ id: 'dataQuery.form.rank.tooltip' })} className="ml-1">
                <span className="text-gray-400 dark:text-gray-500" aria-label={intl.formatMessage({ id: 'dataQuery.form.rank.tooltipAria' })}>
                  ?
                </span>
              </Tooltip>
            </span>
            <input
              type="number"
              aria-label={intl.formatMessage({ id: 'dataQuery.form.rank.label' })}
              value={values.rank}
              onChange={(event) => onChange({ rank: Number(event.target.value) })}
              className="min-h-[48px] rounded-lg border border-gray-200 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
            />
          </label>
        )}

        {showKeyword && (
          <label className="flex flex-col gap-1 md:col-span-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {keywordLabel}
              <Tooltip label={intl.formatMessage({ id: 'dataQuery.form.keyword.tooltip' })} className="ml-1">
                <span className="text-gray-400 dark:text-gray-500" aria-label={intl.formatMessage({ id: 'dataQuery.form.keyword.tooltipAria' })}>
                  ?
                </span>
              </Tooltip>
            </span>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400 dark:text-gray-500" aria-hidden="true" />
              <input
                type="text"
                aria-label={intl.formatMessage({ id: 'dataQuery.form.fieldAria' }, { title, field: keywordLabel })}
                value={values.keyword}
                onChange={(event) => onChange({ keyword: event.target.value })}
                placeholder={meta.keywordPlaceholderKey ? intl.formatMessage({ id: meta.keywordPlaceholderKey }) : undefined}
                className="min-h-[48px] w-full rounded-lg border border-gray-200 py-2 pl-9 pr-3 text-sm dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
              />
            </div>
          </label>
        )}
      </div>
    </section>
  );
}
