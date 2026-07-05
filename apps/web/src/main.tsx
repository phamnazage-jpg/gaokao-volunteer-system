/**
 * V10 option B · application entry (Vite 5 + React 19).
 *
 * - QueryClient: TanStack Query 5
 * - RouterProvider: React Router 7, replacing Next.js App Router.
 * - Global styles: globals.css.
 */
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { PersistQueryClientProvider } from '@tanstack/react-query-persist-client';
import { RouterProvider } from 'react-router-dom';
import {
  QUERY_CACHE_MAX_AGE_MS,
  createAppQueryClient,
  createLocalStoragePersister,
  queryPersistenceBuster,
} from '@/lib/query-client';
import { AppIntlProvider } from '@/i18n/AppIntlProvider';
import { Toaster } from '@/components/shared/Toast';
import { router } from './router';
import './styles/globals.css';

const queryClient = createAppQueryClient();
const persister = createLocalStoragePersister(window.localStorage);

const rootEl = document.getElementById('root');
if (!rootEl) {
  throw new Error('Root element #root not found');
}

createRoot(rootEl).render(
  <StrictMode>
    <PersistQueryClientProvider
      client={queryClient}
      persistOptions={{
        persister,
        maxAge: QUERY_CACHE_MAX_AGE_MS,
        buster: queryPersistenceBuster,
      }}
      onSuccess={() => {
        void queryClient.resumePausedMutations().then(() => {
          void queryClient.invalidateQueries();
        });
      }}
    >
      <AppIntlProvider>
        <RouterProvider router={router} />
        <Toaster />
        {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
      </AppIntlProvider>
    </PersistQueryClientProvider>
  </StrictMode>,
);
