import { useState } from 'react';
import { Image as ImageIcon } from 'lucide-react';
import { FormattedMessage } from 'react-intl';
import { usePosterGenerateMutation, usePosterStatusQuery } from '@/hooks/usePosterGenerate';
import { PosterPreview, type PosterTemplate } from '@/components/PosterPreview';

export function PosterPreviewPage() {
  const [template, setTemplate] = useState<PosterTemplate>('classic');
  const generate = usePosterGenerateMutation();
  const posterStatus = usePosterStatusQuery(generate.data?.jobId ?? null);
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
    generate.mutate({ planId: 'plan-sample-001', template });
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
      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
        <FormattedMessage id="poster.page.description" />
      </p>

      <PosterPreview
        template={template}
        statusSnapshot={statusSnapshot}
        isGenerating={generate.isPending}
        isGenerateError={generate.isError || posterStatus.isError}
        onTemplateChange={setTemplate}
        onGenerate={handleGenerate}
        onCopyQrCode={handleCopyQrCode}
      />
    </div>
  );
}
