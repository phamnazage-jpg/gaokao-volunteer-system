import zhCN from './messages/zh-CN.json';
import enUS from './messages/en-US.json';

export type AppLocale = 'zh-CN' | 'en-US';

export const DEFAULT_LOCALE: AppLocale = 'zh-CN';

export const messages: Record<AppLocale, Record<string, string>> = {
  'zh-CN': zhCN,
  'en-US': enUS,
};

export const localeOptions: ReadonlyArray<{ value: AppLocale; labelKey: string }> = [
  { value: 'zh-CN', labelKey: 'app.language.zh' },
  { value: 'en-US', labelKey: 'app.language.en' },
];
