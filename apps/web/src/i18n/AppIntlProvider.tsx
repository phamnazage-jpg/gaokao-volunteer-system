import type { ReactNode } from 'react';
import { IntlProvider } from 'react-intl';
import { DEFAULT_LOCALE, messages } from './messages';
import { useUIStore } from '@/stores/ui';

interface AppIntlProviderProps {
  children: ReactNode;
}

export function AppIntlProvider({ children }: AppIntlProviderProps) {
  const locale = useUIStore((state) => state.locale);

  return (
    <IntlProvider locale={locale} defaultLocale={DEFAULT_LOCALE} messages={messages[locale]} onError={() => undefined}>
      {children}
    </IntlProvider>
  );
}
