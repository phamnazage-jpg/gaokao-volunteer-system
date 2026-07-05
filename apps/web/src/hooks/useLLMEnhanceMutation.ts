/**
 * V10 · Sprint 3 · useAuditEnhanceMutation + useLLMConfig
 */
import { useMutation, useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { enhanceWithFallback, DEFAULT_FALLBACK_ORDER, type AuditInput, type AuditEnhancement, type ProviderId } from '@/lib/llm/provider';
import { apiClient } from '@/lib/api-client';

export const LLMConfigSchema = z.object({
  currentProvider: z.enum(['claude', 'gpt', 'gemini', 'deepseek']),
  fallbackOrder: z.array(z.enum(['claude', 'gpt', 'gemini', 'deepseek'])),
  availableProviders: z.array(z.enum(['claude', 'gpt', 'gemini', 'deepseek'])),
});

export const AuditEnhanceStatusSchema = z.object({
  planId: z.string(),
  status: z.enum(['queued', 'processing', 'completed', 'failed']),
  progress: z.number().int().min(0).max(100),
  currentStep: z.string(),
  updatedAt: z.string(),
});

export type LLMConfigResponse = z.infer<typeof LLMConfigSchema>;
export type AuditEnhanceStatusResponse = z.infer<typeof AuditEnhanceStatusSchema>;

export interface EnhanceResult {
  readonly result: AuditEnhancement;
  readonly usedProvider: ProviderId;
  readonly fallbackCount: number;
}

export const llmKeys = {
  all: ['llm'] as const,
  config: () => [...llmKeys.all, 'config'] as const,
  enhanceStatus: (planId: string) => [...llmKeys.all, 'enhance-status', planId] as const,
};

export function useLLMConfig() {
  return useQuery<LLMConfigResponse>({
    queryKey: llmKeys.config(),
    queryFn: () => apiClient.get<LLMConfigResponse>('/llm/config', LLMConfigSchema),
    staleTime: 5 * 60 * 1000,
  });
}

export function useAuditEnhanceStatusQuery(planId: string | null) {
  return useQuery<AuditEnhanceStatusResponse>({
    queryKey: planId ? llmKeys.enhanceStatus(planId) : [...llmKeys.all, 'enhance-status', 'noop'],
    queryFn: () => apiClient.get<AuditEnhanceStatusResponse>(`/llm/enhance/${planId}/status`, AuditEnhanceStatusSchema),
    enabled: Boolean(planId),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && (data.status === 'completed' || data.status === 'failed')) return false;
      return 2000;
    },
  });
}

export function useAuditEnhanceMutation(preferredOrder?: ReadonlyArray<ProviderId>) {
  return useMutation<EnhanceResult, Error, AuditInput>({
    mutationFn: async (input) => {
      const order = preferredOrder ?? DEFAULT_FALLBACK_ORDER;
      let lastErr: Error | null = null;
      for (let i = 0; i < order.length; i++) {
        const providerId = order[i];
        try {
          const { result, usedProvider } = await enhanceWithFallback(input, [providerId]);
          return {
            result,
            usedProvider,
            fallbackCount: i,
          };
        } catch (err) {
          lastErr = err instanceof Error ? err : new Error(String(err));
        }
      }
      throw lastErr ?? new Error('LLM call failed');
    },
  });
}
