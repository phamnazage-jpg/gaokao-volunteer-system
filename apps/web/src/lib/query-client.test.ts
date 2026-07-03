import { describe, expect, it, beforeEach } from 'vitest';
import { persistQueryClientRestore, persistQueryClientSave } from '@tanstack/react-query-persist-client';
import {
  QUERY_CACHE_MAX_AGE_MS,
  createAppQueryClient,
  createLocalStoragePersister,
  queryPersistenceBuster,
} from './query-client';
import { dataQueryKeys } from '@/hooks/useDataQuery';
import { llmKeys } from '@/hooks/useLLMEnhanceMutation';
import { planKeys } from '@/hooks/usePlanQueries';
import { reviewKeys } from '@/hooks/useReviewFlow';
import { shareLinkKeys } from '@/hooks/useShareLink';

describe('query persistence config', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('uses a 4 hour cache retention window for persisted queries', () => {
    const queryClient = createAppQueryClient();

    expect(QUERY_CACHE_MAX_AGE_MS).toBe(4 * 60 * 60 * 1000);
    expect(queryClient.getDefaultOptions().queries?.gcTime).toBe(QUERY_CACHE_MAX_AGE_MS);
    expect(queryClient.getDefaultOptions().queries?.staleTime).toBe(60 * 1000);
    expect(queryClient.getDefaultOptions().queries?.refetchOnWindowFocus).toBe(false);
  });

  it('creates a localStorage persister compatible with TanStack restore/save', () => {
    const persister = createLocalStoragePersister(window.localStorage);

    expect(persister.persistClient).toEqual(expect.any(Function));
    expect(persister.restoreClient).toEqual(expect.any(Function));
    expect(persister.removeClient).toEqual(expect.any(Function));
  });

  it('restores cached queries for five existing modules after a refresh', async () => {
    const sourceClient = createAppQueryClient();
    const persister = createLocalStoragePersister(window.localStorage);

    const cachedQueries = [
      [shareLinkKeys.latest(), { code: 'ABC123', url: 'https://example.test/s/ABC123' }],
      [dataQueryKeys.schools('计算机'), { schools: [{ id: 's1', name: '中山大学' }], total: 1 }],
      [reviewKeys.status('review-1'), { id: 'review-1', status: 'approved' }],
      [llmKeys.config(), { currentProvider: 'gpt', fallbackOrder: ['gpt'], availableProviders: ['gpt'] }],
      [planKeys.list(), { plans: [{ id: 'plan-1', title: '广东物理方案' }], total: 1 }],
    ] as const;

    for (const [key, value] of cachedQueries) {
      sourceClient.setQueryData(key, value);
    }

    await persistQueryClientSave({
      queryClient: sourceClient,
      persister,
      buster: queryPersistenceBuster,
    });

    const restoredClient = createAppQueryClient();
    await persistQueryClientRestore({
      queryClient: restoredClient,
      persister,
      maxAge: QUERY_CACHE_MAX_AGE_MS,
      buster: queryPersistenceBuster,
    });

    for (const [key, value] of cachedQueries) {
      expect(restoredClient.getQueryData(key)).toEqual(value);
    }
  });
});
