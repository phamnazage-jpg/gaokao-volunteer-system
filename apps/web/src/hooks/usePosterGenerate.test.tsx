import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { usePosterStatusQuery } from './usePosterGenerate';
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

describe('usePosterStatusQuery', () => {
  it('polls poster generation status by job id', async () => {
    server.use(
      http.get('/api/poster/:jobId/status', ({ params }) => {
        return HttpResponse.json({
          jobId: params['jobId'],
          status: 'processing',
          progress: 40,
          posterUrl: null,
          qrCode: null,
          expiresAt: null,
          updatedAt: '2026-07-04T00:00:00.000Z',
        });
      }),
    );

    const { result } = renderHook(() => usePosterStatusQuery('poster-1'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toMatchObject({
      jobId: 'poster-1',
      status: 'processing',
      progress: 40,
    });
  });
});
