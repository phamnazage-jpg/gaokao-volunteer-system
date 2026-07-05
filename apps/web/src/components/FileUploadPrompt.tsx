import { FormattedMessage } from 'react-intl';
import type { FileUploadPromptMessageData } from '@/types/message';

interface Props {
  data: FileUploadPromptMessageData;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function FileUploadPrompt({ data }: Props) {
  return (
    <div className="mt-2 bg-white border border-dashed border-blue-300 rounded-2xl rounded-tl-md shadow-sm p-4 dark:border-blue-500/40 dark:bg-gray-900">
      <div className="text-center mb-3">
        <div className="text-3xl mb-2">📎</div>
        <h4 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
          <FormattedMessage id="fileUploadPrompt.title" />
        </h4>
        <p className="text-xs text-gray-500 mt-1 dark:text-gray-400">
          <FormattedMessage id="fileUploadPrompt.meta" values={{ formats: data.acceptedFormats.map((f) => f.toUpperCase()).join(' / '), size: formatSize(data.maxSize) }} />
        </p>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          className="py-3 bg-blue-50 border border-blue-200 rounded-xl text-sm text-blue-700 hover:bg-blue-100 transition-colors dark:border-blue-500/30 dark:bg-blue-500/10 dark:text-blue-200 dark:hover:bg-blue-500/20"
        >
          <FormattedMessage id="fileUploadPrompt.actions.pasteText" />
        </button>
        <button
          type="button"
          className="py-3 bg-green-50 border border-green-200 rounded-xl text-sm text-green-700 hover:bg-green-100 transition-colors dark:border-green-500/30 dark:bg-green-500/10 dark:text-green-200 dark:hover:bg-green-500/20"
        >
          <FormattedMessage id="fileUploadPrompt.actions.uploadSheet" />
        </button>
        <button
          type="button"
          className="py-3 bg-purple-50 border border-purple-200 rounded-xl text-sm text-purple-700 hover:bg-purple-100 transition-colors dark:border-purple-500/30 dark:bg-purple-500/10 dark:text-purple-200 dark:hover:bg-purple-500/20"
        >
          <FormattedMessage id="fileUploadPrompt.actions.uploadImage" />
        </button>
        <button
          type="button"
          className="py-3 bg-orange-50 border border-orange-200 rounded-xl text-sm text-orange-700 hover:bg-orange-100 transition-colors dark:border-orange-500/30 dark:bg-orange-500/10 dark:text-orange-200 dark:hover:bg-orange-500/20"
        >
          <FormattedMessage id="fileUploadPrompt.actions.uploadPdf" />
        </button>
      </div>
    </div>
  );
}
