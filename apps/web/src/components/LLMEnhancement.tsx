import { useMemo, useState } from 'react';
import { Sparkles } from 'lucide-react';
import { FormattedMessage, useIntl } from 'react-intl';
import { useAuditEnhanceMutation, useLLMConfig, type AuditEnhanceStatusResponse } from '@/hooks/useLLMEnhanceMutation';
import type { ProviderId } from '@/lib/llm/provider';

type EnhancementType = 'detail' | 'risk' | 'suggestion';

interface LLMEnhancementProps {
  planId: string | null;
  status?: AuditEnhanceStatusResponse;
  enhancementType?: EnhancementType;
}

const PROVIDER_LABELS: Record<ProviderId, string> = {
  claude: 'Claude',
  gpt: 'GPT-4o',
  gemini: 'Gemini',
  deepseek: 'DeepSeek',
};

const PRIORITY_LABEL_KEYS = {
  low: 'llmEnhancement.priority.low',
  medium: 'llmEnhancement.priority.medium',
  high: 'llmEnhancement.priority.high',
} as const;

const DEFAULT_PROVIDERS: ProviderId[] = ['claude', 'gpt', 'gemini', 'deepseek'];

export function LLMEnhancement({ planId, status, enhancementType = 'detail' }: LLMEnhancementProps) {
  const intl = useIntl();
  const config = useLLMConfig();
  const providers = config.data?.availableProviders.length ? config.data.availableProviders : DEFAULT_PROVIDERS;
  const [preferredProvider, setPreferredProvider] = useState<ProviderId>(providers[0] ?? 'claude');
  const preferredOrder = useMemo(
    () => [preferredProvider, ...providers.filter((provider) => provider !== preferredProvider)],
    [preferredProvider, providers],
  );
  const enhance = useAuditEnhanceMutation(preferredOrder);

  const canEnhance = Boolean(planId) && !enhance.isPending;

  const handleEnhance = (): void => {
    if (!planId) return;
    enhance.mutate({ planId, enhancementType });
  };

  return (
    <section
      className="rounded-xl border border-blue-100 bg-blue-50/40 p-6 shadow-sm dark:border-blue-900/60 dark:bg-blue-950/30"
      aria-label={intl.formatMessage({ id: 'llmEnhancement.panel.ariaLabel' })}
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <Sparkles className="mt-1 h-5 w-5 text-blue-600" aria-hidden="true" />
          <div>
            <p className="text-sm font-semibold text-blue-950 dark:text-blue-100">
              <FormattedMessage id="llmEnhancement.panel.title" />
            </p>
            <p className="mt-1 text-sm text-blue-800 dark:text-blue-300">
              <FormattedMessage id="llmEnhancement.panel.description" />
            </p>
          </div>
        </div>
        <div className="flex flex-col gap-2 sm:min-w-44">
          <label className="text-xs font-medium text-blue-900 dark:text-blue-200" htmlFor="llm-provider">
            <FormattedMessage id="llmEnhancement.provider.label" />
          </label>
          <select
            id="llm-provider"
            value={preferredProvider}
            onChange={(event) => setPreferredProvider(event.target.value as ProviderId)}
            className="min-h-[40px] rounded-lg border border-blue-200 bg-white px-3 py-2 text-sm text-blue-950 dark:border-blue-900 dark:bg-gray-900 dark:text-blue-100"
          >
            {providers.map((provider) => (
              <option key={provider} value={provider}>
                {PROVIDER_LABELS[provider]}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={handleEnhance}
            disabled={!canEnhance}
            className="min-h-[40px] rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
          >
            <FormattedMessage id={enhance.isPending ? 'llmEnhancement.action.enhancing' : 'llmEnhancement.action.trigger'} />
          </button>
        </div>
      </div>

      {status && (
        <div className="mt-4 rounded-xl bg-white p-4 dark:bg-gray-900" role="region" aria-label={intl.formatMessage({ id: 'llmEnhancement.status.ariaLabel' })}>
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs text-gray-400 dark:text-gray-500">
                <FormattedMessage id="llmEnhancement.status.currentStep" />
              </p>
              <p className="text-sm font-medium text-gray-800 dark:text-gray-100">{status.currentStep}</p>
            </div>
            <p className="text-sm font-semibold text-blue-700 dark:text-blue-300">{status.progress}%</p>
          </div>
          <div
            className="mt-3 h-2 rounded-full bg-gray-100 dark:bg-gray-800"
            role="progressbar"
            aria-label={intl.formatMessage({ id: 'llmEnhancement.status.progressAriaLabel' })}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={status.progress}
          >
            <div className="h-full rounded-full bg-blue-600 transition-[width]" style={{ width: `${status.progress}%` }} />
          </div>
        </div>
      )}

      {enhance.isError && (
        <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300" role="alert">
          <p className="font-semibold">
            <FormattedMessage id="llmEnhancement.error.title" />
          </p>
          <p className="mt-1">
            <FormattedMessage id="llmEnhancement.error.description" />
          </p>
        </div>
      )}

      {enhance.data && (
        <div className="mt-4 rounded-xl bg-white p-4 dark:bg-gray-900" role="region" aria-label={intl.formatMessage({ id: 'llmEnhancement.result.ariaLabel' })}>
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">{enhance.data.result.summary}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              <FormattedMessage
                id="llmEnhancement.result.providerMeta"
                values={{ provider: PROVIDER_LABELS[enhance.data.usedProvider], count: enhance.data.fallbackCount }}
              />
            </p>
          </div>
          <ul className="mt-3 space-y-3">
            {enhance.data.result.recommendations.map((item) => (
              <li key={item.title} className="rounded-lg border border-gray-100 p-3 dark:border-gray-800">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{item.title}</p>
                  <span className="rounded-full bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 dark:bg-blue-950/50 dark:text-blue-300">
                    <FormattedMessage id="llmEnhancement.result.priority" values={{ priority: intl.formatMessage({ id: PRIORITY_LABEL_KEYS[item.priority] }) }} />
                  </span>
                </div>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">{item.detail}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
