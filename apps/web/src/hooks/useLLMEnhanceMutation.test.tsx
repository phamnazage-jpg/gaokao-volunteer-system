import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { useAuditEnhanceStatusQuery } from './useLLMEnhanceMutation';
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

describe('useAuditEnhanceStatusQuery', () => {
  it('polls the backend LLM enhance status endpoint', async () => {
    server.use(
      http.get('/api/llm/enhance/:planId/status', ({ params }) => {
        return HttpResponse.json({
          planId: params['planId'],
          status: 'processing',
          progress: 60,
          currentStep: '生成风险建议',
          updatedAt: '2026-07-04T00:00:00.000Z',
        });
      }),
    );

    const { result } = renderHook(() => useAuditEnhanceStatusQuery('plan-001'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toMatchObject({
      planId: 'plan-001',
      status: 'processing',
      progress: 60,
      currentStep: '生成风险建议',
    });
  });
});
