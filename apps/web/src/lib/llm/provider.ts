/**
 * V10 · Sprint 3 · LLM Provider 适配器
 *
 * 4 模 provider 抽象：claude / gpt / gemini / deepseek
 * 接口：enhance(input: AuditInput) → Promise<AuditEnhancement>
 *
 * V10 G2 闸门核心：4 provider 实测可切换 + 自动降级
 */
import type { z } from 'zod';
import { AuditEnhanceInputSchema, AuditEnhancementSchema } from '@/lib/api-schemas';

export type AuditInput = z.infer<typeof AuditEnhanceInputSchema>;
export type AuditEnhancement = z.infer<typeof AuditEnhancementSchema>;

export type ProviderId = 'claude' | 'gpt' | 'gemini' | 'deepseek';

export interface LLMProvider {
  readonly id: ProviderId;
  readonly displayName: string;
  enhance(input: AuditInput, signal?: AbortSignal): Promise<AuditEnhancement>;
}

export class ProviderError extends Error {
  constructor(
    public readonly providerId: ProviderId,
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ProviderError';
  }
}

class ClaudeProvider implements LLMProvider {
  readonly id = 'claude' as const;
  readonly displayName = 'Claude';
  async enhance(input: AuditInput, signal?: AbortSignal): Promise<AuditEnhancement> {
    const res = await fetch('/api/llm/claude/enhance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
      signal,
    });
    if (!res.ok) throw new ProviderError('claude', res.status, `Claude 调用失败: ${res.status}`);
    return AuditEnhancementSchema.parse(await res.json());
  }
}

class GPTProvider implements LLMProvider {
  readonly id = 'gpt' as const;
  readonly displayName = 'GPT-4o';
  async enhance(input: AuditInput, signal?: AbortSignal): Promise<AuditEnhancement> {
    const res = await fetch('/api/llm/gpt/enhance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
      signal,
    });
    if (!res.ok) throw new ProviderError('gpt', res.status, `GPT 调用失败: ${res.status}`);
    return AuditEnhancementSchema.parse(await res.json());
  }
}

class GeminiProvider implements LLMProvider {
  readonly id = 'gemini' as const;
  readonly displayName = 'Gemini';
  async enhance(input: AuditInput, signal?: AbortSignal): Promise<AuditEnhancement> {
    const res = await fetch('/api/llm/gemini/enhance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
      signal,
    });
    if (!res.ok) throw new ProviderError('gemini', res.status, `Gemini 调用失败: ${res.status}`);
    return AuditEnhancementSchema.parse(await res.json());
  }
}

class DeepseekProvider implements LLMProvider {
  readonly id = 'deepseek' as const;
  readonly displayName = 'DeepSeek';
  async enhance(input: AuditInput, signal?: AbortSignal): Promise<AuditEnhancement> {
    const res = await fetch('/api/llm/deepseek/enhance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
      signal,
    });
    if (!res.ok) throw new ProviderError('deepseek', res.status, `DeepSeek 调用失败: ${res.status}`);
    return AuditEnhancementSchema.parse(await res.json());
  }
}

export const PROVIDERS: Readonly<Record<ProviderId, LLMProvider>> = {
  claude: new ClaudeProvider(),
  gpt: new GPTProvider(),
  gemini: new GeminiProvider(),
  deepseek: new DeepseekProvider(),
};

/**
 * 4 模 fallback 链: claude → gpt → gemini → deepseek
 */
export const DEFAULT_FALLBACK_ORDER: ReadonlyArray<ProviderId> = ['claude', 'gpt', 'gemini', 'deepseek'];

export async function enhanceWithFallback(
  input: AuditInput,
  order: ReadonlyArray<ProviderId> = DEFAULT_FALLBACK_ORDER,
  signal?: AbortSignal,
): Promise<{ result: AuditEnhancement; usedProvider: ProviderId }> {
  let lastError: Error | null = null;
  for (const providerId of order) {
    if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');
    try {
      const result = await PROVIDERS[providerId].enhance(input, signal);
      return { result, usedProvider: providerId };
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
    }
  }
  throw lastError ?? new Error('所有 LLM provider 均失败');
}