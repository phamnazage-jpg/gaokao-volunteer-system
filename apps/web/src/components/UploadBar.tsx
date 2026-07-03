'use client';

import React, { useRef, useState } from 'react';

interface Props {
  onUpload: (type: 'text' | 'excel' | 'image' | 'pdf', file?: File, textContent?: string) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

const UPLOAD_OPTIONS = [
  { type: 'excel' as const, label: 'Excel', icon: '📊', desc: '上传 .xlsx/.xls', accept: '.xlsx,.xls', color: 'border-green-300 bg-green-50 text-green-700 hover:bg-green-100' },
  { type: 'image' as const, label: '图片', icon: '📷', desc: '拍照/截图上传', accept: 'image/*', color: 'border-purple-300 bg-purple-50 text-purple-700 hover:bg-purple-100' },
  { type: 'pdf' as const, label: 'PDF', icon: '📄', desc: '上传 PDF 文件', accept: '.pdf', color: 'border-orange-300 bg-orange-50 text-orange-700 hover:bg-orange-100' },
  { type: 'text' as const, label: '粘贴', icon: '📝', desc: '直接粘贴方案文本', accept: undefined, color: 'border-blue-300 bg-blue-50 text-blue-700 hover:bg-blue-100' },
];

export function UploadBar({ onUpload, collapsed = false, onToggleCollapse }: Props) {
  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({});
  const [pasteMode, setPasteMode] = useState(false);
  const [pasteText, setPasteText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleFileSelect = (type: 'excel' | 'image' | 'pdf') => {
    const option = UPLOAD_OPTIONS.find(o => o.type === type);
    if (!option?.accept) return;
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = option.accept;
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        // Size check
        const maxSize = type === 'excel' ? 5 * 1024 * 1024 : 10 * 1024 * 1024;
        if (file.size > maxSize) {
          alert(`文件过大，${option.label}文件不能超过 ${maxSize / 1024 / 1024}MB`);
          return;
        }
        onUpload(type, file);
      }
    };
    input.click();
  };

  const handlePasteSubmit = () => {
    const text = pasteText.trim();
    if (!text) return;
    onUpload('text', undefined, text);
    setPasteText('');
    setPasteMode(false);
  };

  if (pasteMode) {
    return (
      <div className="px-4 py-3 bg-blue-50/50 border-t border-blue-100">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-gray-700">📝 粘贴你的志愿方案文本</span>
          <button onClick={() => setPasteMode(false)} className="text-xs text-gray-400 hover:text-gray-600">取消</button>
        </div>
        <textarea
          ref={textareaRef}
          value={pasteText}
          onChange={e => setPasteText(e.target.value)}
          placeholder="在这里粘贴你的志愿方案（院校-专业列表），例如：&#10;1. 华南理工大学 计算机类&#10;2. 中山大学 电子信息类&#10;..."
          rows={4}
          className="w-full border border-blue-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          autoFocus
        />
        <div className="flex justify-end mt-2">
          <button
            onClick={handlePasteSubmit}
            disabled={!pasteText.trim()}
            className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-all ${
              pasteText.trim()
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            提交审核
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-2.5 bg-gray-50/80 border-t border-gray-100">
      {/* Compact bar header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-500">📎 审核志愿方案</span>
          <span className="hidden sm:inline text-[10px] text-gray-400">— 上传或粘贴你的方案，我来帮你审核</span>
        </div>
        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
            aria-label={collapsed ? '展开上传选项' : '收起上传选项'}
          >
            {collapsed ? '展开 ▼' : '收起 ▲'}
          </button>
        )}
      </div>

      {/* Upload options grid */}
      {!collapsed && (
        <div className="grid grid-cols-4 gap-2 mt-2">
          {UPLOAD_OPTIONS.map(option => (
            option.accept ? (
              <button
                key={option.type}
                onClick={() => handleFileSelect(option.type as 'excel' | 'image' | 'pdf')}
                className={`flex flex-col items-center gap-1 py-2.5 rounded-xl border text-xs font-medium transition-colors min-h-[56px] ${option.color}`}
              >
                <span className="text-base sm:text-lg">{option.icon}</span>
                <span className="hidden sm:inline">{option.label}</span>
                <span className="text-[9px] opacity-60 hidden sm:inline">{option.desc}</span>
              </button>
            ) : (
              <button
                key={option.type}
                onClick={() => setPasteMode(true)}
                className={`flex flex-col items-center gap-1 py-2.5 rounded-xl border text-xs font-medium transition-colors min-h-[56px] ${option.color}`}
              >
                <span className="text-base sm:text-lg">{option.icon}</span>
                <span className="hidden sm:inline">{option.label}</span>
                <span className="text-[9px] opacity-60 hidden sm:inline">{option.desc}</span>
              </button>
            )
          ))}
        </div>
      )}

      {collapsed && (
        <p className="text-[10px] text-gray-400 mt-1.5">
          点击「展开」选择上传方式，或在输入框直接粘贴方案文本
        </p>
      )}
    </div>
  );
}
