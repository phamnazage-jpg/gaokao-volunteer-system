import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { useShareLinkCreate, useShareLinkDelete, useShareLinkStatsQuery } from './useShareLink';
import { server } from '@/test/mocks/server';

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe('useShareLink hooks', () => {
  it('normalizes the backend share-link payload for the frontend', async () => {
    const { result } = renderHook(() => useShareLinkCreate(), { wrapper });

    result.current.mutate({ planId: 'portal-token-1', expiresIn: 30 });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toMatchObject({
      id: 'ABC123',
      code: 'ABC123',
      url: 'https://example.test/s/ABC123',
      planId: 'portal-token-1',
      revoked: false,
    });
  });

  it('retries a transient create failure once before succeeding', async () => {
    let attempts = 0;
    server.use(
      http.post('/api/share-link', () => {
        attempts += 1;
        if (attempts === 1) {
          return HttpResponse.json({ message: 'temporary unavailable' }, { status: 503 });
        }
        return HttpResponse.json(
          {
            code: 'RETRY1',
            share_url: 'https://example.test/s/RETRY1',
            target_id: 'portal-token-1',
            expires_at_iso: null,
            revoked: false,
          },
          { status: 201 },
        );
      }),
    );

    const { result } = renderHook(() => useShareLinkCreate(), { wrapper });

    result.current.mutate({ planId: 'portal-token-1', expiresIn: 30 });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.code).toBe('RETRY1');
    expect(attempts).toBe(2);
  });

  it('revokes by code through the backend revoke endpoint', async () => {
    const { result } = renderHook(() => useShareLinkDelete(), { wrapper });

    result.current.mutate('ABC123');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual({ success: true });
  });

  it('reads share-link stats without unhandled MSW warnings', async () => {
    const { result } = renderHook(() => useShareLinkStatsQuery('ABC123'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual({
      views: 12,
      uniqueVisitors: 5,
      lastAccessedAt: '2026-07-03T00:00:00.000Z',
    });
  });
});
