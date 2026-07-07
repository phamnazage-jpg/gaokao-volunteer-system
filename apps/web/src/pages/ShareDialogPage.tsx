import { useState } from 'react';
import { Share2 } from 'lucide-react';
import { FormattedMessage, useIntl } from 'react-intl';
import { useShareLinkLatestQuery } from '@/hooks/useShareLink';
import { ShareDialog } from '@/components/ShareDialog';
import { ShareStatusPanel } from '@/components/ShareStatusPanel';


export function ShareDialogPage() {
  const intl = useIntl();
  const [open, setOpen] = useState(false);
  const latest = useShareLinkLatestQuery();
  const selectedPlanId = latest.data?.planId ?? '';
  const selectedPlanTitle = selectedPlanId
    ? intl.formatMessage({ id: 'share.page.selectedPlanTitle' }, { planId: selectedPlanId })
    : intl.formatMessage({ id: 'share.page.noPlanSelectedTitle' });

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2 dark:text-gray-100">
        <Share2 className="w-6 h-6" aria-hidden="true" />
        <FormattedMessage id="share.page.title" />
      </h1>
      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
        <FormattedMessage id="share.page.description" />
      </p>

      <div className="mt-6 grid gap-4">
        <ShareStatusPanel
          latest={latest.data}
          isLoading={latest.isLoading}
          isError={latest.isError}
          trend={[]}
          onCreate={() => setOpen(true)}
          onRetry={() => void latest.refetch()}
        />

        <button
          type="button"
          onClick={() => setOpen(true)}
          className="w-full min-h-[48px] py-3 rounded-xl bg-blue-600 text-white font-medium hover:bg-blue-700"
        >
          <FormattedMessage id={latest.data ? 'share.page.newLink' : 'share.page.createLink'} />
        </button>
      </div>

      <ShareDialog
        planId={selectedPlanId}
        planTitle={selectedPlanTitle}
        open={open}
        onClose={() => setOpen(false)}
      />
    </div>
  );
}
