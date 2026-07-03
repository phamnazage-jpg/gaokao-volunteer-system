/**
 * V10 · Sprint 3 · ShareDialog
 *
 * 分享弹窗：QR Code + 链接 + 复制 + 海报生成入口
 * V10 不变量：移动端 48px 触发区
 */
import { useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { X, Copy, Check, Share2 } from 'lucide-react';
import { useShareLinkCreate, useShareLinkDelete, useShareLinkStatsQuery } from '@/hooks/useShareLink';
import { usePosterGenerateMutation } from '@/hooks/usePosterGenerate';

interface Props {
  planId: string;
  planTitle: string;
  open: boolean;
  onClose: () => void;
}

export function ShareDialog({ planId, planTitle, open, onClose }: Props) {
  const [copied, setCopied] = useState(false);
  const create = useShareLinkCreate();
  const del = useShareLinkDelete();
  const posterGen = usePosterGenerateMutation();
  const code = create.data?.code ?? null;
  const stats = useShareLinkStatsQuery(code);

  if (!open) return null;

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
        // 剪贴板不可用
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
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
      aria-label="分享方案"
      tabIndex={-1}
      onClick={onClose}
      onKeyDown={(e) => {
        if (e.key === 'Escape') onClose();
      }}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white shadow-2xl p-6"
        role="document"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <Share2 className="w-5 h-5" aria-hidden="true" />
            分享方案
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="w-10 h-10 min-w-[48px] min-h-[48px] flex items-center justify-center rounded-lg hover:bg-gray-100"
            aria-label="关闭"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-sm text-gray-500 mb-4">{planTitle}</p>

        {!create.data ? (
          <div className="flex flex-col gap-3">
            <button
              type="button"
              onClick={handleCreate}
              disabled={create.isPending}
              className="w-full min-h-[48px] py-3 rounded-xl bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {create.isPending ? '创建中…' : '创建分享链接（30天有效）'}
            </button>
            <button
              type="button"
              onClick={handleGeneratePoster}
              disabled={posterGen.isPending}
              className="w-full min-h-[48px] py-3 rounded-xl bg-white text-gray-700 border border-gray-200 font-medium hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              {posterGen.isPending ? '生成中…' : posterGen.data ? '查看海报' : '生成分享海报'}
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <div className="rounded-xl bg-white p-3 border border-gray-100">
              <QRCodeSVG value={create.data.url} size={180} level="M" />
            </div>
            <div className="w-full flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={create.data.url}
                className="flex-1 px-3 py-2 text-xs bg-gray-50 border border-gray-200 rounded-lg truncate"
                aria-label="分享链接"
              />
              <button
                type="button"
                onClick={handleCopy}
                className="min-w-[48px] min-h-[48px] px-3 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center hover:bg-blue-100"
                aria-label="复制链接"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>

            {stats.data && (
              <div className="w-full grid grid-cols-3 gap-2 text-center text-xs">
                <div className="rounded-lg bg-gray-50 px-2 py-2">
                  <p className="text-gray-400">访问数</p>
                  <p className="font-semibold text-gray-800">{stats.data.views}</p>
                </div>
                <div className="rounded-lg bg-gray-50 px-2 py-2">
                  <p className="text-gray-400">独立访客</p>
                  <p className="font-semibold text-gray-800">{stats.data.uniqueVisitors}</p>
                </div>
                <div className="rounded-lg bg-gray-50 px-2 py-2">
                  <p className="text-gray-400">最近访问</p>
                  <p className="font-semibold text-gray-800 truncate">
                    {stats.data.lastAccessedAt ? new Date(stats.data.lastAccessedAt).toLocaleDateString() : '—'}
                  </p>
                </div>
              </div>
            )}

            <button
              type="button"
              onClick={handleDelete}
              className="text-xs text-gray-400 hover:text-red-500 transition-colors min-h-[48px] py-2"
            >
              撤销分享链接
            </button>
          </div>
        )}
      </div>
    </div>
  );
}