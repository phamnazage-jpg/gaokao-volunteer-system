/**
 * V10 · Sprint 3 · LLM Provider 单测 (G2 闸门核心)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { enhanceWithFallback, PROVIDERS, DEFAULT_FALLBACK_ORDER, ProviderError } from './provider';

describe('LLM Provider · G2 闸门', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('4 provider types are registered', () => {
    expect(Object.keys(PROVIDERS)).toEqual(['claude', 'gpt', 'gemini', 'deepseek']);
    expect(DEFAULT_FALLBACK_ORDER).toEqual(['claude', 'gpt', 'gemini', 'deepseek']);
  });

  it('uses claude when it succeeds', async () => {
    const mockEnhance = vi.fn().mockResolvedValue({ summary: 'ok', recommendations: [] });
    vi.spyOn(PROVIDERS.claude, 'enhance').mockImplementation(mockEnhance);

    const { result, usedProvider } = await enhanceWithFallback({ planId: 'p1', enhancementType: 'detail' });
    expect(usedProvider).toBe('claude');
    expect(result.summary).toBe('ok');
    expect(mockEnhance).toHaveBeenCalledTimes(1);
  });

  it('falls back from claude to gpt when claude fails', async () => {
    vi.spyOn(PROVIDERS.claude, 'enhance').mockRejectedValue(new ProviderError('claude', 500, 'fail'));
    const gptSpy = vi.spyOn(PROVIDERS.gpt, 'enhance').mockResolvedValue({ summary: 'from-gpt', recommendations: [] });

    const { result, usedProvider } = await enhanceWithFallback({ planId: 'p1', enhancementType: 'detail' });
    expect(usedProvider).toBe('gpt');
    expect(result.summary).toBe('from-gpt');
    expect(gptSpy).toHaveBeenCalledTimes(1);
  });

  it('falls back through all 4 providers and surfaces last error', async () => {
    vi.spyOn(PROVIDERS.claude, 'enhance').mockRejectedValue(new ProviderError('claude', 500, 'claude-fail'));
    vi.spyOn(PROVIDERS.gpt, 'enhance').mockRejectedValue(new ProviderError('gpt', 500, 'gpt-fail'));
    vi.spyOn(PROVIDERS.gemini, 'enhance').mockRejectedValue(new ProviderError('gemini', 500, 'gemini-fail'));
    vi.spyOn(PROVIDERS.deepseek, 'enhance').mockRejectedValue(new ProviderError('deepseek', 500, 'deepseek-fail'));

    await expect(enhanceWithFallback({ planId: 'p1', enhancementType: 'detail' })).rejects.toThrow(/deepseek-fail/);
  });

  it('gemini succeeds when claude and gpt fail', async () => {
    vi.spyOn(PROVIDERS.claude, 'enhance').mockRejectedValue(new ProviderError('claude', 500, 'c'));
    vi.spyOn(PROVIDERS.gpt, 'enhance').mockRejectedValue(new ProviderError('gpt', 500, 'g'));
    vi.spyOn(PROVIDERS.gemini, 'enhance').mockResolvedValue({ summary: 'from-gemini', recommendations: [] });

    const { usedProvider } = await enhanceWithFallback({ planId: 'p1', enhancementType: 'detail' });
    expect(usedProvider).toBe('gemini');
  });
});