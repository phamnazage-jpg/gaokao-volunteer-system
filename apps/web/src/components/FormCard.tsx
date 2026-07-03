/**
 * V10 选项 B · FormCard 组件 (RHF 7 + Zod 重写版)
 *
 * 替代原型 FormCard.tsx 中的手写 3-step 状态机
 *
 * V10 不变量 C3: 3-step guards
 *  - step 1→2: 需 score 输入
 *  - step 2→3: 需选科 + 位次
 *  - 后退保留数据 (RHF 自动)
 */
import { useState } from 'react';
import { useForm, type SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const FormCardSchema = z.object({
  province: z.string().min(1, '请选择省份'),
  score: z.coerce.number().int('请输入整数').min(0, '分数不能小于 0').max(750, '分数不能大于 750'),
  rank: z.coerce.number().int('请输入整数').min(1, '位次必须 ≥ 1'),
  subjects: z.array(z.string()).min(1, '请至少选择 1 个选科'),
});
export type FormCardData = z.infer<typeof FormCardSchema>;

interface FormCardProps {
  onSubmit: (data: FormCardData) => void;
  initialData?: Partial<FormCardData>;
}

const PROVINCES = ['北京', '上海', '广东', '江苏', '浙江', '山东', '河南', '河北', '四川', '湖北', '湖南', '福建', '安徽'];
const SUBJECTS = ['物理', '历史', '化学', '生物', '地理', '政治'];

const STEP_FIELDS: ReadonlyArray<ReadonlyArray<keyof FormCardData>> = [
  ['province'],
  ['score'],
  ['rank', 'subjects'],
] as const;

export function FormCard({ onSubmit, initialData }: FormCardProps) {
  const [step, setStep] = useState(0);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    trigger,
    watch,
    setValue,
    getValues,
  } = useForm<FormCardData>({
    resolver: zodResolver(FormCardSchema),
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

  const handleFormSubmit: SubmitHandler<FormCardData> = (data) => {
    onSubmit(data);
  };

  const toggleSubject = (subject: string): void => {
    const current = getValues('subjects') ?? [];
    const next = current.includes(subject) ? current.filter((s) => s !== subject) : [...current, subject];
    setValue('subjects', next, { shouldValidate: true, shouldDirty: true });
  };

  return (
    <form
      onSubmit={(event) => { void handleSubmit(handleFormSubmit)(event); }}
      className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm"
      aria-label="志愿信息收集"
    >
      {/* 步骤指示器 */}
      <div className="flex items-center justify-between mb-4">
        {['省份', '分数', '位次 / 选科'].map((label, idx) => (
          <div key={label} className="flex items-center flex-1">
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                idx <= step ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
              }`}
            >
              {idx + 1}
            </div>
            <span className={`ml-2 text-xs ${idx <= step ? 'text-gray-800' : 'text-gray-400'}`}>{label}</span>
            {idx < 2 && <div className={`flex-1 h-px mx-2 ${idx < step ? 'bg-blue-600' : 'bg-gray-200'}`} />}
          </div>
        ))}
      </div>

      {/* Step 1: 省份 */}
      {step === 0 && (
        <div>
          <label htmlFor="province" className="block text-sm font-medium text-gray-700 mb-2">
            你的高考省份
          </label>
          <select
            id="province"
            {...register('province')}
            className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">请选择...</option>
            {PROVINCES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
          {errors.province && <p className="mt-1 text-xs text-red-500">{errors.province.message}</p>}
        </div>
      )}

      {/* Step 2: 分数 */}
      {step === 1 && (
        <div>
          <label htmlFor="score" className="block text-sm font-medium text-gray-700 mb-2">
            你的高考分数
          </label>
          <input
            id="score"
            type="number"
            inputMode="numeric"
            {...register('score')}
            placeholder="例如 620"
            className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {errors.score && <p className="mt-1 text-xs text-red-500">{errors.score.message}</p>}
        </div>
      )}

      {/* Step 3: 位次 + 选科 */}
      {step === 2 && (
        <div className="space-y-4">
          <div>
            <label htmlFor="rank" className="block text-sm font-medium text-gray-700 mb-2">
              你的位次
            </label>
            <input
              id="rank"
              type="number"
              inputMode="numeric"
              {...register('rank')}
              placeholder="例如 8500"
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.rank && <p className="mt-1 text-xs text-red-500">{errors.rank.message}</p>}
          </div>

          <div>
            <span className="block text-sm font-medium text-gray-700 mb-2">选科组合</span>
            <div className="flex flex-wrap gap-2">
              {SUBJECTS.map((s) => {
                const active = selectedSubjects.includes(s);
                return (
                  <button
                    key={s}
                    type="button"
                    onClick={() => toggleSubject(s)}
                    className={`px-3 py-1.5 rounded-full text-xs border transition-colors ${
                      active ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'
                    }`}
                  >
                    {s}
                  </button>
                );
              })}
            </div>
            {errors.subjects && <p className="mt-1 text-xs text-red-500">{errors.subjects.message}</p>}
          </div>
        </div>
      )}

      {/* 步骤导航 */}
      <div className="flex items-center justify-between mt-5">
        {step > 0 ? (
          <button
            type="button"
            onClick={handlePrev}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-xl transition-colors"
          >
            ← 上一步
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
            下一步 →
          </button>
        ) : (
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {isSubmitting ? '提交中...' : '生成志愿方案'}
          </button>
        )}
      </div>
    </form>
  );
}