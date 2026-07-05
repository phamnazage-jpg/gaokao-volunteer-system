import { X, Share2 } from 'lucide-react';
import { FormattedMessage, useIntl } from 'react-intl';
import { SharePanel } from './SharePanel';

interface Props {
  planId: string;
  planTitle: string;
  open: boolean;
  onClose: () => void;
}

export function ShareDialog({ planId, planTitle, open, onClose }: Props) {
  const intl = useIntl();
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
      aria-label={intl.formatMessage({ id: 'share.dialog.ariaLabel' })}
      tabIndex={-1}
      onClick={onClose}
      onKeyDown={(e) => {
        if (e.key === 'Escape') onClose();
      }}
    >
      <div
        className="w-full max-w-md rounded-2xl border border-transparent bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900"
        role="document"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2 dark:text-gray-100">
            <Share2 className="w-5 h-5" aria-hidden="true" />
            <FormattedMessage id="share.dialog.title" />
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="w-10 h-10 min-w-[48px] min-h-[48px] flex items-center justify-center rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-gray-100"
            aria-label={intl.formatMessage({ id: 'share.dialog.close' })}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <SharePanel planId={planId} planTitle={planTitle} />
      </div>
    </div>
  );
}
