'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { SavedPlan } from '@/lib/useChat';

export default function PlansPage() {
  const router = useRouter();
  const [plans, setPlans] = useState<SavedPlan[]>([]);
  const [compareMode, setCompareMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<SavedPlan | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem('savedPlans');
      if (raw) setPlans(JSON.parse(raw));
    } catch {}
  }, []);

  const savePlans = useCallback((updated: SavedPlan[]) => {
    setPlans(updated);
    try {
      localStorage.setItem('savedPlans', JSON.stringify(updated));
    } catch {}
  }, []);

  const handleDelete = (plan: SavedPlan) => {
    setDeleteTarget(plan);
  };

  const confirmDelete = () => {
    if (!deleteTarget) return;
    const updated = plans.filter(p => p.id !== deleteTarget.id);
    savePlans(updated);
    setDeleteTarget(null);
    setSelectedIds(prev => prev.filter(id => id !== deleteTarget.id));
  };

  const handleNameEdit = (plan: SavedPlan) => {
    setEditingId(plan.id);
    setEditingName(plan.name);
  };

  const confirmNameEdit = () => {
    if (!editingId || !editingName.trim()) {
      setEditingId(null);
      return;
    }
    const updated = plans.map(p =>
      p.id === editingId ? { ...p, name: editingName.trim() } : p
    );
    savePlans(updated);
    setEditingId(null);
  };

  const toggleSelect = (id: string) => {
    setSelectedIds(prev => {
      if (prev.includes(id)) return prev.filter(x => x !== id);
      if (prev.length >= 2) return prev;
      return [...prev, id];
    });
  };

  const handleCompare = () => {
    if (selectedIds.length === 2) {
      router.push(`/plans/compare?ids=${selectedIds.join(',')}`);
    }
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  };

  const getCategoryCounts = (plan: any) => {
    const rush = plan.rush?.length || 0;
    const stable = plan.stable?.length || 0;
    const safe = plan.safe?.length || 0;
    return { rush, stable, safe };
  };

  if (plans.length === 0) {
    return (
      <div className="flex flex-col min-h-screen max-w-3xl mx-auto bg-white shadow-lg">
        <header className="flex items-center px-4 py-3 border-b border-gray-100 bg-white/95 backdrop-blur sticky top-0 z-10">
          <Link href="/" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span>返回对话</span>
          </Link>
          <h1 className="flex-1 text-center text-sm font-bold text-gray-800 -ml-8">我的方案</h1>
        </header>

        <div className="flex-1 flex flex-col items-center justify-center px-4 py-16">
          <div className="w-32 h-32 bg-gray-100 rounded-full flex items-center justify-center mb-6">
            <svg className="w-16 h-16 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <p className="text-gray-400 text-sm mb-6">还没有保存的方案</p>
          <Link
            href="/"
            className="px-6 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            去创建第一个方案
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen max-w-3xl mx-auto bg-white shadow-lg">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-white/95 backdrop-blur sticky top-0 z-10">
        <Link href="/" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>返回对话</span>
        </Link>
        <h1 className="text-sm font-bold text-gray-800">我的方案</h1>
        <button
          onClick={() => {
            setCompareMode(!compareMode);
            setSelectedIds([]);
          }}
          className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${
            compareMode
              ? 'bg-blue-600 text-white'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
          }`}
        >
          {compareMode ? '取消对比' : '对比方案'}
        </button>
      </header>

      {/* Compare bar */}
      {compareMode && (
        <div className="px-4 py-2 bg-blue-50 border-b border-blue-100 flex items-center justify-between">
          <p className="text-xs text-blue-700">
            {selectedIds.length === 0
              ? '请勾选2个方案进行对比'
              : selectedIds.length === 1
              ? '已选1个，请再选1个方案'
              : `已选${selectedIds.length}个方案`}
          </p>
          <button
            onClick={handleCompare}
            disabled={selectedIds.length !== 2}
            className={`text-xs px-4 py-1.5 rounded-lg transition-colors ${
              selectedIds.length === 2
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
          >
            开始对比
          </button>
        </div>
      )}

      {/* Plan list */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {plans.map(plan => {
          const { rush, stable, safe } = getCategoryCounts(plan.plan);
          const isSelected = selectedIds.includes(plan.id);
          return (
            <div
              key={plan.id}
              className={`bg-white border rounded-xl shadow-sm overflow-hidden transition-colors ${
                isSelected && compareMode
                  ? 'border-blue-400 ring-2 ring-blue-100'
                  : 'border-gray-200'
              }`}
            >
              {/* Card header */}
              <div className="px-4 py-3">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    {editingId === plan.id ? (
                      <input
                        type="text"
                        value={editingName}
                        onChange={e => setEditingName(e.target.value)}
                        onBlur={confirmNameEdit}
                        onKeyDown={e => {
                          if (e.key === 'Enter') confirmNameEdit();
                          if (e.key === 'Escape') setEditingId(null);
                        }}
                        className="text-sm font-semibold text-gray-800 border border-blue-300 rounded px-2 py-0.5 focus:outline-none focus:ring-2 focus:ring-blue-500 w-full"
                        autoFocus
                      />
                    ) : (
                      <h3
                        className="text-sm font-semibold text-gray-800 truncate cursor-pointer hover:text-blue-600"
                        onClick={() => handleNameEdit(plan)}
                        title="点击编辑名称"
                      >
                        {plan.name}
                      </h3>
                    )}
                    <p className="text-xs text-gray-400 mt-0.5">{formatDate(plan.createdAt)}</p>
                  </div>
                  {compareMode && (
                    <div
                      onClick={() => toggleSelect(plan.id)}
                      className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 cursor-pointer ml-2 ${
                        isSelected
                          ? 'bg-blue-600 border-blue-600'
                          : 'border-gray-300'
                      }`}
                    >
                      {isSelected && (
                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                  )}
                </div>

                {/* Profile info */}
                <p className="text-xs text-gray-500 mt-2">
                  {plan.profile.province || '—'} · {plan.profile.subjects?.join('+') || '—'} · {plan.profile.score || '—'}分 · 位次{plan.profile.rank || '—'}
                </p>

                {/* Category distribution */}
                <div className="flex gap-3 mt-2">
                  <span className="text-xs text-orange-600 bg-orange-50 px-2 py-0.5 rounded">🚀 冲刺{rush}所</span>
                  <span className="text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded">✅ 稳妥{stable}所</span>
                  <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded">🛡️ 保底{safe}所</span>
                </div>
              </div>

              {/* Actions */}
              <div className="px-4 py-2.5 bg-gray-50 border-t border-gray-100 flex gap-2">
                <Link
                  href={`/plans/${plan.id}`}
                  className="flex-1 py-1.5 bg-white border border-gray-200 rounded-lg text-xs font-medium text-gray-600 hover:bg-gray-100 transition-colors text-center"
                >
                  查看详情
                </Link>
                <Link
                  href={`/plans/${plan.id}?action=export`}
                  className="flex-1 py-1.5 bg-white border border-gray-200 rounded-lg text-xs font-medium text-gray-600 hover:bg-gray-100 transition-colors text-center"
                >
                  导出
                </Link>
                <button
                  onClick={() => {
                    if (selectedIds.length < 2) {
                      toggleSelect(plan.id);
                    }
                    if (selectedIds.length === 2 || (selectedIds.length === 1 && !selectedIds.includes(plan.id))) {
                      setCompareMode(true);
                      toggleSelect(plan.id);
                    }
                  }}
                  className="flex-1 py-1.5 bg-white border border-gray-200 rounded-lg text-xs font-medium text-gray-600 hover:bg-gray-100 transition-colors"
                >
                  对比
                </button>
                <button
                  onClick={() => handleDelete(plan)}
                  className="flex-1 py-1.5 bg-white border border-red-200 rounded-lg text-xs font-medium text-red-500 hover:bg-red-50 transition-colors"
                >
                  删除
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Delete confirmation dialog */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
          <div className="bg-white rounded-2xl shadow-xl p-6 max-w-sm w-full">
            <h3 className="text-sm font-semibold text-gray-800 mb-2">确认删除</h3>
            <p className="text-sm text-gray-500 mb-6">
              确定要删除方案「{deleteTarget.name}」吗？删除后不可恢复
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteTarget(null)}
                className="flex-1 py-2 bg-gray-100 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
              >
                取消
              </button>
              <button
                onClick={confirmDelete}
                className="flex-1 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition-colors"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
