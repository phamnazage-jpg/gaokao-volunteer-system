import { useRef, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';

export type UploadType = 'text' | 'excel' | 'image' | 'pdf';

interface Props {
  onUpload: (type: UploadType, file?: File, textContent?: string) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

interface UploadOption {
  readonly type: UploadType;
  readonly labelKey: string;
  readonly icon: string;
  readonly descriptionKey: string;
  readonly accept: string | undefined;
  readonly color: string;
}

const UPLOAD_OPTIONS: ReadonlyArray<UploadOption> = [
  { type: 'excel', labelKey: 'uploadBar.options.excel.label', icon: '📊', descriptionKey: 'uploadBar.options.excel.description', accept: '.xlsx,.xls', color: 'border-green-300 bg-green-50 text-green-700 hover:bg-green-100' },
  { type: 'image', labelKey: 'uploadBar.options.image.label', icon: '📷', descriptionKey: 'uploadBar.options.image.description', accept: 'image/*', color: 'border-purple-300 bg-purple-50 text-purple-700 hover:bg-purple-100' },
  { type: 'pdf', labelKey: 'uploadBar.options.pdf.label', icon: '📄', descriptionKey: 'uploadBar.options.pdf.description', accept: '.pdf', color: 'border-orange-300 bg-orange-50 text-orange-700 hover:bg-orange-100' },
  { type: 'text', labelKey: 'uploadBar.options.text.label', icon: '📝', descriptionKey: 'uploadBar.options.text.description', accept: undefined, color: 'border-blue-300 bg-blue-50 text-blue-700 hover:bg-blue-100' },
];

export function UploadBar({ onUpload, collapsed = false, onToggleCollapse }: Props) {
  const intl = useIntl();
  const [pasteMode, setPasteMode] = useState(false);
  const [pasteText, setPasteText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleFileSelect = (type: UploadType): void => {
    const option = UPLOAD_OPTIONS.find((o) => o.type === type);
    if (!option?.accept) return;

    const input = document.createElement('input');
    input.type = 'file';
    input.accept = option.accept;
    input.onchange = (e: Event) => {
      const target = e.target as HTMLInputElement;
      const file = target.files?.[0];
      if (file) onUpload(type, file);
    };
    input.click();
  };

  const handleTextSubmit = (): void => {
    if (!pasteText.trim()) return;
    onUpload('text', undefined, pasteText);
    setPasteText('');
    setPasteMode(false);
  };

  if (collapsed) return null;

  return (
    <div className="px-4 py-2 bg-gray-50 border-t border-gray-100 dark:border-gray-800 dark:bg-gray-900" data-testid="upload-bar">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-500 dark:text-gray-400">
          <FormattedMessage id="uploadBar.title" />
        </span>
        {onToggleCollapse && (
          <button
            type="button"
            onClick={onToggleCollapse}
            className="text-xs text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
            aria-label={intl.formatMessage({ id: 'uploadBar.collapse' })}
          >
            ✕
          </button>
        )}
      </div>

      {pasteMode ? (
        <div className="space-y-2">
          <textarea
            ref={textareaRef}
            value={pasteText}
            onChange={(e) => setPasteText(e.target.value)}
            placeholder={intl.formatMessage({ id: 'uploadBar.pastePlaceholder' })}
            rows={3}
            className="w-full border border-gray-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => {
                setPasteMode(false);
                setPasteText('');
              }}
              className="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <FormattedMessage id="uploadBar.cancel" />
            </button>
            <button
              type="button"
              onClick={handleTextSubmit}
              className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <FormattedMessage id="uploadBar.submit" />
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-4 gap-2">
          {UPLOAD_OPTIONS.map((option) => (
            <button
              key={option.type}
              type="button"
              onClick={() => {
                if (option.type === 'text') setPasteMode(true);
                else handleFileSelect(option.type);
              }}
              className={`p-2 border rounded-lg text-xs transition-colors ${option.color} dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:hover:bg-gray-800`}
              title={intl.formatMessage({ id: option.descriptionKey })}
              aria-label={intl.formatMessage({ id: 'uploadBar.optionAriaLabel' }, { label: intl.formatMessage({ id: option.labelKey }) })}
            >
              <div className="text-base mb-0.5">{option.icon}</div>
              <div>
                <FormattedMessage id={option.labelKey} />
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
