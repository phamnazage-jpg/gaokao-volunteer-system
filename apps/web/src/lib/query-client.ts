import { QueryClient } from '@tanstack/react-query';
import { createAsyncStoragePersister } from '@tanstack/query-async-storage-persister';

export const QUERY_CACHE_MAX_AGE_MS = 4 * 60 * 60 * 1000;
export const QUERY_STALE_TIME_MS = 60 * 1000;
export const queryPersistenceBuster = 'v10-sprint-4';

export function createAppQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        gcTime: QUERY_CACHE_MAX_AGE_MS,
        staleTime: QUERY_STALE_TIME_MS,
        refetchOnWindowFocus: false,
        retry: 1,
      },
      mutations: {
        retry: 0,
      },
    },
  });
}

export function createLocalStoragePersister(storage: Storage) {
  return createAsyncStoragePersister({
    storage,
    key: `gaokao-query-cache::${queryPersistenceBuster}`,
  });
}
