/**
 * V10 选项 B · 应用入口 (Vite 5 + React 19)
 *
 * - QueryClient: TanStack Query 5
 * - RouterProvider: React Router 7 (替代 Next.js App Router)
 * - 全局样式: globals.css
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
      <RouterProvider router={router} />
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </PersistQueryClientProvider>
  </StrictMode>,
);
