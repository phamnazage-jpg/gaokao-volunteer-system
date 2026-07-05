import { useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { QRCodeSVG } from 'qrcode.react';
import { Check, Copy } from 'lucide-react';
import { useShareLinkCreate, useShareLinkDelete, useShareLinkStatsQuery } from '@/hooks/useShareLink';
import { usePosterGenerateMutation } from '@/hooks/usePosterGenerate';

interface SharePanelProps {
  planId: string;
  planTitle: string;
}

export function SharePanel({ planId, planTitle }: SharePanelProps) {
  const intl = useIntl();
  const [copied, setCopied] = useState(false);
  const create = useShareLinkCreate();
  const del = useShareLinkDelete();
  const posterGen = usePosterGenerateMutation();
  const code = create.data?.code ?? null;
  const stats = useShareLinkStatsQuery(code);

  const handleCreate = (): void => {
    create.mutate({ planId, expiresIn: 30 });
  };

  const handleCopy = (): void => {
    if (!create.data?.url) return;
    void navigator.clipboard
      .writeText(create.data.url)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      })
      .catch(() => {
        // Clipboard may be unavailable in restricted browsers.
      });
  };

  const handleDelete = (): void => {
    if (!create.data?.id) return;
    del.mutate(create.data.id, {
      onSuccess: () => create.reset(),
    });
  };

  const handleGeneratePoster = (): void => {
    posterGen.mutate({ planId, template: 'classic' });
  };

  return (
    <section aria-label={intl.formatMessage({ id: 'share.panel.ariaLabel' })}>
      <p className="mb-4 text-sm text-gray-500 dark:text-gray-400">{planTitle}</p>

      {!create.data ? (
        <div className="flex flex-col gap-3">
          {create.isError && (
            <div className="rounded-lg border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300" role="alert">
              <FormattedMessage id="share.panel.createError" />
            </div>
          )}
          <button
            type="button"
            onClick={handleCreate}
            disabled={create.isPending}
            className="w-full min-h-[48px] py-3 rounded-xl bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <FormattedMessage id={create.isPending ? 'share.panel.creating' : create.isError ? 'share.panel.retryCreate' : 'share.panel.createWithExpiry'} />
          </button>
          <button
            type="button"
            onClick={handleGeneratePoster}
            disabled={posterGen.isPending}
            className="w-full min-h-[48px] py-3 rounded-xl bg-white text-gray-700 border border-gray-200 font-medium hover:bg-gray-50 disabled:opacity-50 transition-colors dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200 dark:hover:bg-gray-800"
          >
            <FormattedMessage id={posterGen.isPending ? 'share.panel.generatingPoster' : posterGen.data ? 'share.panel.viewPoster' : 'share.panel.generatePoster'} />
          </button>
          {posterGen.isError && (
            <div className="rounded-lg border border-amber-100 bg-amber-50 px-3 py-2 text-sm text-amber-700 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-300" role="alert">
              <FormattedMessage id="share.panel.posterError" />
            </div>
          )}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4">
          <div className="rounded-xl bg-white p-3 border border-gray-100 dark:border-gray-700 dark:bg-gray-900">
            <QRCodeSVG value={create.data.url} size={180} level="M" />
          </div>
          <div className="w-full flex items-center gap-2">
            <input
              type="text"
              readOnly
              value={create.data.url}
              className="flex-1 px-3 py-2 text-xs bg-gray-50 border border-gray-200 rounded-lg truncate dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
              aria-label={intl.formatMessage({ id: 'share.panel.linkAriaLabel' })}
            />
            <button
              type="button"
              onClick={handleCopy}
              className="min-w-[48px] min-h-[48px] px-3 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center hover:bg-blue-100 dark:bg-blue-950/50 dark:text-blue-300 dark:hover:bg-blue-900/60"
              aria-label={intl.formatMessage({ id: 'share.panel.copyLink' })}
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>

          {stats.isError && (
            <div className="w-full rounded-lg border border-amber-100 bg-amber-50 px-3 py-2 text-sm text-amber-700 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-300" role="status">
              <FormattedMessage id="share.panel.statsUnavailable" />
            </div>
          )}

          {stats.data && (
            <div className="w-full grid grid-cols-3 gap-2 text-center text-xs">
              <div className="rounded-lg bg-gray-50 px-2 py-2 dark:bg-gray-800">
                <p className="text-gray-400 dark:text-gray-500">
                  <FormattedMessage id="share.stats.views" />
                </p>
                <p className="font-semibold text-gray-800 dark:text-gray-100">{stats.data.views}</p>
              </div>
              <div className="rounded-lg bg-gray-50 px-2 py-2 dark:bg-gray-800">
                <p className="text-gray-400 dark:text-gray-500">
                  <FormattedMessage id="share.stats.uniqueVisitors" />
                </p>
                <p className="font-semibold text-gray-800 dark:text-gray-100">{stats.data.uniqueVisitors}</p>
              </div>
              <div className="rounded-lg bg-gray-50 px-2 py-2 dark:bg-gray-800">
                <p className="text-gray-400 dark:text-gray-500">
                  <FormattedMessage id="share.stats.lastAccessed" />
                </p>
                <p className="font-semibold text-gray-800 truncate dark:text-gray-100">
                  {stats.data.lastAccessedAt ? intl.formatDate(new Date(stats.data.lastAccessedAt), { dateStyle: 'short' }) : '—'}
                </p>
              </div>
            </div>
          )}

          <button
            type="button"
            onClick={handleDelete}
            className="text-xs text-gray-400 hover:text-red-500 transition-colors min-h-[48px] py-2 dark:text-gray-500 dark:hover:text-red-300"
          >
            <FormattedMessage id="share.panel.revoke" />
          </button>
          {del.isError && (
            <p className="text-xs text-red-500 dark:text-red-300" role="alert">
              <FormattedMessage id="share.panel.revokeError" />
            </p>
          )}
        </div>
      )}
    </section>
  );
}
