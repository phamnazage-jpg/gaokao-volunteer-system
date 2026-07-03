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

export type LLMConfigResponse = z.infer<typeof LLMConfigSchema>;

export interface EnhanceResult {
  readonly result: AuditEnhancement;
  readonly usedProvider: ProviderId;
  readonly fallbackCount: number;
}

export const llmKeys = {
  all: ['llm'] as const,
  config: () => [...llmKeys.all, 'config'] as const,
};

export function useLLMConfig() {
  return useQuery<LLMConfigResponse>({
    queryKey: llmKeys.config(),
    queryFn: () => apiClient.get<LLMConfigResponse>('/llm/config', LLMConfigSchema),
    staleTime: 5 * 60 * 1000,
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
      throw lastErr ?? new Error('LLM 调用失败');
    },
  });
}