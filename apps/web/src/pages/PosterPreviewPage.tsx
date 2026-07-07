import { useState } from 'react';
import { Image as ImageIcon } from 'lucide-react';
import { FormattedMessage } from 'react-intl';
import { usePosterGenerateMutation, usePosterStatusQuery } from '@/hooks/usePosterGenerate';
import { usePlansQuery } from '@/hooks/usePlanQueries';
import { PosterPreview, type PosterTemplate } from '@/components/PosterPreview';

export function PosterPreviewPage() {
  const [template, setTemplate] = useState<PosterTemplate>('classic');
  const generate = usePosterGenerateMutation();
  const posterStatus = usePosterStatusQuery(generate.data?.jobId ?? null);
  const plansQuery = usePlansQuery();
  const selectedPlanId = plansQuery.data?.plans[0]?.id ?? null;
  const statusSnapshot = posterStatus.data ?? (generate.data?.jobId
    ? {
        jobId: generate.data.jobId,
        status: generate.data.status ?? 'queued',
        progress: generate.data.progress ?? 0,
        posterUrl: generate.data.posterUrl ?? null,
        qrCode: generate.data.qrCode ?? null,
        expiresAt: generate.data.expiresAt ?? null,
      }
    : null);

  const handleGenerate = (): void => {
    if (!selectedPlanId) return;
    generate.mutate({ planId: selectedPlanId, template });
  };

  const handleCopyQrCode = (qrCode: string): void => {
    void navigator.clipboard?.writeText(qrCode);
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2 dark:text-gray-100">
        <ImageIcon className="w-6 h-6" aria-hidden="true" />
        <FormattedMessage id="poster.page.title" />
      </h1>

      {!selectedPlanId && !plansQuery.isLoading && (
        <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200" role="alert">
          <FormattedMessage id="poster.status.selectPlan" />
        </div>
      )}
      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
        <FormattedMessage id="poster.page.description" />
      </p>

      <PosterPreview
        template={template}
        statusSnapshot={statusSnapshot}
        isGenerating={generate.isPending}
        isGenerateError={generate.isError || posterStatus.isError}
        isGenerateDisabled={!selectedPlanId || plansQuery.isLoading}
        onTemplateChange={setTemplate}
        onGenerate={handleGenerate}
        onCopyQrCode={handleCopyQrCode}
      />
    </div>
  );
}
