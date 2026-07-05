import { useIntl } from 'react-intl';
import { localeOptions, type AppLocale } from '@/i18n/messages';
import { useUIStore } from '@/stores/ui';

export function LocaleSwitcher() {
  const intl = useIntl();
  const locale = useUIStore((state) => state.locale);
  const setLocale = useUIStore((state) => state.setLocale);

  return (
    <label className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 text-sm font-medium text-slate-600 shadow-sm focus-within:ring-2 focus-within:ring-blue-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
      <span>{intl.formatMessage({ id: 'app.language' })}</span>
      <select
        value={locale}
        onChange={(event) => setLocale(event.target.value as AppLocale)}
        className="bg-transparent text-sm font-semibold text-slate-950 outline-none dark:text-white"
        aria-label={intl.formatMessage({ id: 'app.language' })}
      >
        {localeOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {intl.formatMessage({ id: option.labelKey })}
          </option>
        ))}
      </select>
    </label>
  );
}
