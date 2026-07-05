import { useMemo, useState } from 'react';
import { useForm, type SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { FormattedMessage, useIntl, type IntlShape } from 'react-intl';
import { SubmitButton } from '@/components/shared/SubmitButton';
import { Stepper, type StepperStep } from '@/components/shared/Stepper';

function createFormCardSchema(intl: IntlShape) {
  return z.object({
    province: z.string().min(1, intl.formatMessage({ id: 'formCard.validation.province' })),
    score: z.coerce
      .number()
      .int(intl.formatMessage({ id: 'formCard.validation.integer' }))
      .min(0, intl.formatMessage({ id: 'formCard.validation.scoreMin' }))
      .max(750, intl.formatMessage({ id: 'formCard.validation.scoreMax' })),
    rank: z.coerce
      .number()
      .int(intl.formatMessage({ id: 'formCard.validation.integer' }))
      .min(1, intl.formatMessage({ id: 'formCard.validation.rankMin' })),
    subjects: z.array(z.string()).min(1, intl.formatMessage({ id: 'formCard.validation.subjects' })),
  });
}

type FormCardSchema = ReturnType<typeof createFormCardSchema>;
export type FormCardData = z.infer<FormCardSchema>;

interface FormCardProps {
  onSubmit: (data: FormCardData) => void | Promise<void>;
  initialData?: Partial<FormCardData>;
}

const PROVINCE_KEYS = [
  'beijing',
  'shanghai',
  'guangdong',
  'jiangsu',
  'zhejiang',
  'shandong',
  'henan',
  'hebei',
  'sichuan',
  'hubei',
  'hunan',
  'fujian',
  'anhui',
] as const;
const SUBJECT_KEYS = ['physics', 'history', 'chemistry', 'biology', 'geography', 'politics'] as const;

const STEP_FIELDS: ReadonlyArray<ReadonlyArray<keyof FormCardData>> = [
  ['province'],
  ['score'],
  ['rank', 'subjects'],
] as const;

export function FormCard({ onSubmit, initialData }: FormCardProps) {
  const intl = useIntl();
  const [step, setStep] = useState(0);
  const schema = useMemo(() => createFormCardSchema(intl), [intl]);
  const formSteps: StepperStep[] = useMemo(
    () => [
      { key: 'province', label: intl.formatMessage({ id: 'formCard.steps.province' }) },
      { key: 'score', label: intl.formatMessage({ id: 'formCard.steps.score' }) },
      { key: 'rank-subjects', label: intl.formatMessage({ id: 'formCard.steps.rankSubjects' }) },
    ],
    [intl],
  );
  const provinceOptions = useMemo(
    () =>
      PROVINCE_KEYS.map((key) => ({
        value: intl.formatMessage({ id: `formCard.provinces.${key}` }),
        label: intl.formatMessage({ id: `formCard.provinces.${key}` }),
      })),
    [intl],
  );
  const subjectOptions = useMemo(
    () =>
      SUBJECT_KEYS.map((key) => ({
        value: intl.formatMessage({ id: `formCard.subjects.${key}` }),
        label: intl.formatMessage({ id: `formCard.subjects.${key}` }),
      })),
    [intl],
  );

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    trigger,
    watch,
    setValue,
    getValues,
  } = useForm<FormCardData>({
    resolver: zodResolver(schema),
    defaultValues: {
      province: initialData?.province ?? '',
      score: initialData?.score,
      rank: initialData?.rank,
      subjects: initialData?.subjects ?? [],
    },
    mode: 'onBlur',
  });

  const selectedSubjects = watch('subjects') ?? [];

  const handleNext = async (): Promise<void> => {
    const fields = STEP_FIELDS[step] ?? [];
    const valid = await trigger([...fields]);
    if (valid) setStep((s) => Math.min(s + 1, 2));
  };

  const handlePrev = (): void => {
    setStep((s) => Math.max(s - 1, 0));
  };

  const handleFormSubmit: SubmitHandler<FormCardData> = async (data) => {
    await onSubmit(data);
  };

  const toggleSubject = (subject: string): void => {
    const current = getValues('subjects') ?? [];
    const next = current.includes(subject) ? current.filter((s) => s !== subject) : [...current, subject];
    setValue('subjects', next, { shouldValidate: true, shouldDirty: true });
  };

  return (
    <form
      onSubmit={(event) => { void handleSubmit(handleFormSubmit)(event); }}
      className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900"
      aria-label={intl.formatMessage({ id: 'formCard.ariaLabel' })}
    >
      <Stepper steps={formSteps} currentIndex={step} label={intl.formatMessage({ id: 'formCard.stepperLabel' })} className="mb-4" />

      {step === 0 && (
        <div>
          <label htmlFor="province" className="block text-sm font-medium text-gray-700 mb-2 dark:text-gray-300">
            <FormattedMessage id="formCard.fields.province" />
          </label>
          <select
            id="province"
            {...register('province')}
            className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
          >
            <option value="">{intl.formatMessage({ id: 'formCard.fields.provincePlaceholder' })}</option>
            {provinceOptions.map((province) => (
              <option key={province.value} value={province.value}>
                {province.label}
              </option>
            ))}
          </select>
          {errors.province && <p className="mt-1 text-xs text-red-500 dark:text-red-300">{errors.province.message}</p>}
        </div>
      )}

      {step === 1 && (
        <div>
          <label htmlFor="score" className="block text-sm font-medium text-gray-700 mb-2 dark:text-gray-300">
            <FormattedMessage id="formCard.fields.score" />
          </label>
          <input
            id="score"
            type="number"
            inputMode="numeric"
            {...register('score')}
            placeholder={intl.formatMessage({ id: 'formCard.fields.scorePlaceholder' })}
            className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 dark:placeholder:text-gray-500"
          />
          {errors.score && <p className="mt-1 text-xs text-red-500 dark:text-red-300">{errors.score.message}</p>}
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <div>
            <label htmlFor="rank" className="block text-sm font-medium text-gray-700 mb-2 dark:text-gray-300">
              <FormattedMessage id="formCard.fields.rank" />
            </label>
            <input
              id="rank"
              type="number"
              inputMode="numeric"
              {...register('rank')}
              placeholder={intl.formatMessage({ id: 'formCard.fields.rankPlaceholder' })}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 dark:placeholder:text-gray-500"
            />
            {errors.rank && <p className="mt-1 text-xs text-red-500 dark:text-red-300">{errors.rank.message}</p>}
          </div>

          <div>
            <span className="block text-sm font-medium text-gray-700 mb-2 dark:text-gray-300">
              <FormattedMessage id="formCard.fields.subjects" />
            </span>
            <div className="flex flex-wrap gap-2">
              {subjectOptions.map((subject) => {
                const active = selectedSubjects.includes(subject.value);
                return (
                  <button
                    key={subject.value}
                    type="button"
                    onClick={() => toggleSubject(subject.value)}
                    className={`px-3 py-1.5 rounded-full text-xs border transition-colors ${
                      active ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:border-blue-400'
                    }`}
                  >
                    {subject.label}
                  </button>
                );
              })}
            </div>
            {errors.subjects && <p className="mt-1 text-xs text-red-500 dark:text-red-300">{errors.subjects.message}</p>}
          </div>
        </div>
      )}

      <div className="flex items-center justify-between mt-5">
        {step > 0 ? (
          <button
            type="button"
            onClick={handlePrev}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-xl transition-colors dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-gray-100"
          >
            <FormattedMessage id="formCard.actions.previous" />
          </button>
        ) : (
          <span />
        )}

        {step < 2 ? (
          <button
            type="button"
            onClick={() => { void handleNext(); }}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors"
          >
            <FormattedMessage id="formCard.actions.next" />
          </button>
        ) : (
          <SubmitButton
            isSubmitting={isSubmitting}
            idleLabel={intl.formatMessage({ id: 'formCard.actions.submit' })}
            submittingLabel={intl.formatMessage({ id: 'formCard.actions.submitting' })}
            className="bg-blue-600 text-white hover:bg-blue-700"
          />
        )}
      </div>
    </form>
  );
}
