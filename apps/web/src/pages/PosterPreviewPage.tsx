/**
 * V10 · Sprint 3 · PosterPreviewPage
 * 海报预览页：模板选择 + 生成 + 预览
 */
import { useState } from 'react';
import { Image as ImageIcon, Download, Share2 } from 'lucide-react';
import { usePosterGenerateMutation } from '@/hooks/usePosterGenerate';
import type { z } from 'zod';
import { PosterGenerateInputSchema } from '@/hooks/usePosterGenerate';

type Template = z.infer<typeof PosterGenerateInputSchema>['template'];

const TEMPLATES: ReadonlyArray<{ id: Template; name: string; gradient: string }> = [
  { id: 'classic', name: '经典', gradient: 'from-blue-500 to-purple-600' },
  { id: 'modern', name: '现代', gradient: 'from-emerald-500 to-cyan-600' },
  { id: 'minimal', name: '简约', gradient: 'from-gray-700 to-gray-900' },
];

export function PosterPreviewPage() {
  const [template, setTemplate] = useState<Template>('classic');
  const generate = usePosterGenerateMutation();

  const handleGenerate = (): void => {
    generate.mutate({ planId: 'plan-sample-001', template });
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
        <ImageIcon className="w-6 h-6" aria-hidden="true" />
        海报生成
      </h1>
      <p className="mt-1 text-sm text-gray-500">选择模板，生成你的方案分享海报</p>

      <div className="mt-6 grid grid-cols-3 gap-3">
        {TEMPLATES.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTemplate(t.id)}
            aria-pressed={template === t.id}
            className={`relative h-32 rounded-xl overflow-hidden border-2 transition-all ${
              template === t.id ? 'border-blue-500 scale-[1.02]' : 'border-transparent'
            }`}
          >
            <div className={`absolute inset-0 bg-gradient-to-br ${t.gradient}`} />
            <span className="absolute inset-0 flex items-center justify-center text-white font-medium">
              {t.name}
            </span>
          </button>
        ))}
      </div>

      <button
        type="button"
        onClick={handleGenerate}
        disabled={generate.isPending}
        className="mt-6 w-full min-h-[48px] py-3 rounded-xl bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
      >
        {generate.isPending ? '生成中…' : <><Share2 className="w-4 h-4" /> 生成海报</>}
      </button>

      {generate.data && (
        <div className="mt-6 rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
          <p className="text-xs font-semibold text-gray-400 mb-3">预览</p>
          <div className={`aspect-[3/4] rounded-xl overflow-hidden bg-gradient-to-br ${TEMPLATES.find((t) => t.id === template)?.gradient ?? 'from-blue-500 to-purple-600'} flex items-center justify-center`}>
            <img
              src={generate.data.posterUrl}
              alt="海报预览"
              className="w-full h-full object-cover"
            />
          </div>
          <div className="mt-4 flex gap-2">
            <a
              href={generate.data.posterUrl}
              download
              className="flex-1 min-h-[48px] py-3 rounded-xl bg-blue-600 text-white text-center font-medium hover:bg-blue-700 flex items-center justify-center gap-2"
            >
              <Download className="w-4 h-4" /> 下载
            </a>
            <button
              type="button"
              onClick={() => {
                if (generate.data) {
                  void navigator.clipboard?.writeText(generate.data.qrCode);
                }
              }}
              className="flex-1 min-h-[48px] py-3 rounded-xl border border-gray-200 text-gray-700 font-medium hover:bg-gray-50"
            >
              复制二维码
            </button>
          </div>
          <p className="mt-2 text-xs text-gray-400 text-center">
            链接有效期至 {new Date(generate.data.expiresAt).toLocaleString('zh-CN', { hour12: false })}
          </p>
        </div>
      )}
    </div>
  );
}