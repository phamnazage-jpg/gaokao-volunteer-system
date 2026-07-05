import { Download, Share2 } from 'lucide-react';
import { FormattedMessage, useIntl } from 'react-intl';
import type { PosterGenerateInput, PosterGenerateResponse, PosterStatusResponse } from '@/hooks/usePosterGenerate';

export type PosterTemplate = PosterGenerateInput['template'];
type PosterSnapshot = PosterGenerateResponse | PosterStatusResponse;

interface PosterPreviewProps {
  template: PosterTemplate;
  statusSnapshot: PosterSnapshot | null;
  isGenerating?: boolean;
  isGenerateError?: boolean;
  onTemplateChange: (template: PosterTemplate) => void;
  onGenerate: () => void;
  onCopyQrCode?: (qrCode: string) => void;
}

const TEMPLATES: ReadonlyArray<{ id: PosterTemplate; nameKey: string; gradient: string }> = [
  { id: 'classic', nameKey: 'poster.template.classic', gradient: 'from-blue-500 to-purple-600' },
  { id: 'modern', nameKey: 'poster.template.modern', gradient: 'from-emerald-500 to-cyan-600' },
  { id: 'minimal', nameKey: 'poster.template.minimal', gradient: 'from-gray-700 to-gray-900' },
];

export function PosterPreview({
  template,
  statusSnapshot,
  isGenerating = false,
  isGenerateError = false,
  onTemplateChange,
  onGenerate,
  onCopyQrCode,
}: PosterPreviewProps) {
  const intl = useIntl();
  const isPosterPending = statusSnapshot?.status === 'queued' || statusSnapshot?.status === 'processing';
  const isPosterFailed = statusSnapshot?.status === 'failed' || isGenerateError;
  const completedPoster = statusSnapshot?.status === 'completed' || (!statusSnapshot?.jobId && statusSnapshot?.posterUrl) ? statusSnapshot : null;
  const previewUrl = completedPoster?.posterUrl ?? null;
  const qrCode = completedPoster?.qrCode ?? null;
  const expiresAt = completedPoster?.expiresAt ?? null;
  const activeGradient = TEMPLATES.find((item) => item.id === template)?.gradient ?? 'from-blue-500 to-purple-600';

  return (
    <section aria-label={intl.formatMessage({ id: 'poster.preview.ariaLabel' })}>
      <div className="mt-6 grid grid-cols-3 gap-3">
        {TEMPLATES.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => onTemplateChange(item.id)}
            aria-pressed={template === item.id}
            className={`relative h-32 overflow-hidden rounded-xl border-2 transition-all ${
              template === item.id ? 'scale-[1.02] border-blue-500 dark:border-blue-300' : 'border-transparent'
            }`}
          >
            <div className={`absolute inset-0 bg-gradient-to-br ${item.gradient}`} />
            <span className="absolute inset-0 flex items-center justify-center font-medium text-white">
              <FormattedMessage id={item.nameKey} />
            </span>
          </button>
        ))}
      </div>

      <button
        type="button"
        onClick={onGenerate}
        disabled={isGenerating || isPosterPending}
        className="mt-6 flex min-h-[48px] w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-3 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {isGenerating || isPosterPending ? (
          <FormattedMessage id="poster.action.generating" />
        ) : (
          <>
            <Share2 className="h-4 w-4" aria-hidden="true" /> <FormattedMessage id="poster.action.generate" />
          </>
        )}
      </button>

      {statusSnapshot && isPosterPending && (
        <div className="mt-6 rounded-xl border border-gray-100 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900" role="region" aria-label={intl.formatMessage({ id: 'poster.status.ariaLabel' })}>
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold text-gray-400 dark:text-gray-500">
                <FormattedMessage id="poster.status.generating" />
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                <FormattedMessage id="poster.status.description" />
              </p>
            </div>
            <p className="text-sm font-semibold text-blue-700 dark:text-blue-300">{statusSnapshot.progress ?? 0}%</p>
          </div>
          <div
            className="mt-3 h-2 rounded-full bg-gray-100 dark:bg-gray-800"
            role="progressbar"
            aria-label={intl.formatMessage({ id: 'poster.status.progressAriaLabel' })}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={statusSnapshot.progress ?? 0}
          >
            <div className="h-full rounded-full bg-blue-600 transition-[width]" style={{ width: `${statusSnapshot.progress ?? 0}%` }} />
          </div>
        </div>
      )}

      {isPosterFailed && (
        <div className="mt-6 rounded-lg border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300" role="alert">
          <FormattedMessage id="poster.status.failed" />
        </div>
      )}

      {previewUrl && qrCode && expiresAt && (
        <div className="mt-6 rounded-xl border border-gray-100 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900" role="region" aria-label={intl.formatMessage({ id: 'poster.result.ariaLabel' })}>
          <p className="mb-3 text-xs font-semibold text-gray-400 dark:text-gray-500">
            <FormattedMessage id="poster.result.preview" />
          </p>
          <div className={`flex aspect-[3/4] items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br ${activeGradient}`}>
            <img src={previewUrl} alt={intl.formatMessage({ id: 'poster.result.imageAlt' })} className="h-full w-full object-cover" />
          </div>
          <div className="mt-4 flex gap-2">
            <a
              href={previewUrl}
              download
              className="flex min-h-[48px] flex-1 items-center justify-center gap-2 rounded-xl bg-blue-600 py-3 text-center font-medium text-white hover:bg-blue-700"
            >
              <Download className="h-4 w-4" aria-hidden="true" /> <FormattedMessage id="poster.result.download" />
            </a>
            <button
              type="button"
              onClick={() => onCopyQrCode?.(qrCode)}
              className="min-h-[48px] flex-1 rounded-xl border border-gray-200 py-3 font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
            >
              <FormattedMessage id="poster.result.copyQrCode" />
            </button>
          </div>
          <p className="mt-2 text-center text-xs text-gray-400 dark:text-gray-500">
            <FormattedMessage
              id="poster.result.expiresAt"
              values={{
                date: intl.formatDate(new Date(expiresAt), {
                  year: 'numeric',
                  month: '2-digit',
                  day: '2-digit',
                  hour: '2-digit',
                  minute: '2-digit',
                  hour12: false,
                }),
              }}
            />
          </p>
        </div>
      )}
    </section>
  );
}
