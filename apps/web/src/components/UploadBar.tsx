/**
 * V10 选项 B · UploadBar 组件 (重写, 移除 'use client')
 */
import { useRef, useState } from 'react';

export type UploadType = 'text' | 'excel' | 'image' | 'pdf';

interface Props {
  onUpload: (type: UploadType, file?: File, textContent?: string) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

interface UploadOption {
  readonly type: UploadType;
  readonly label: string;
  readonly icon: string;
  readonly desc: string;
  readonly accept: string | undefined;
  readonly color: string;
}

const UPLOAD_OPTIONS: ReadonlyArray<UploadOption> = [
  { type: 'excel', label: 'Excel', icon: '📊', desc: '上传 .xlsx/.xls', accept: '.xlsx,.xls', color: 'border-green-300 bg-green-50 text-green-700 hover:bg-green-100' },
  { type: 'image', label: '图片', icon: '📷', desc: '拍照/截图上传', accept: 'image/*', color: 'border-purple-300 bg-purple-50 text-purple-700 hover:bg-purple-100' },
  { type: 'pdf', label: 'PDF', icon: '📄', desc: '上传 PDF 文件', accept: '.pdf', color: 'border-orange-300 bg-orange-50 text-orange-700 hover:bg-orange-100' },
  { type: 'text', label: '粘贴', icon: '📝', desc: '直接粘贴方案文本', accept: undefined, color: 'border-blue-300 bg-blue-50 text-blue-700 hover:bg-blue-100' },
];

export function UploadBar({ onUpload, collapsed = false, onToggleCollapse }: Props) {
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
    <div className="px-4 py-2 bg-gray-50 border-t border-gray-100" data-testid="upload-bar">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-500">📎 上传方案文件</span>
        {onToggleCollapse && (
          <button
            type="button"
            onClick={onToggleCollapse}
            className="text-xs text-gray-400 hover:text-gray-600"
            aria-label="收起上传条"
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
            placeholder="粘贴你的志愿方案文本..."
            rows={3}
            className="w-full border border-gray-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => {
                setPasteMode(false);
                setPasteText('');
              }}
              className="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700"
            >
              取消
            </button>
            <button
              type="button"
              onClick={handleTextSubmit}
              className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              提交
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
              className={`p-2 border rounded-lg text-xs transition-colors ${option.color}`}
              title={option.desc}
              aria-label={`上传 ${option.label}`}
            >
              <div className="text-base mb-0.5">{option.icon}</div>
              <div>{option.label}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}