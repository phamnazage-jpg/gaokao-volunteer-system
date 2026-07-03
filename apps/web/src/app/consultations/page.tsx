'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { ConsultationRecord } from '@/lib/useChat';

const RECORDS_KEY = 'consultationRecords';
const ACTIVE_KEY = 'activeConsultationId';

function loadRecords(): ConsultationRecord[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(RECORDS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveRecords(records: ConsultationRecord[]) {
  try {
    localStorage.setItem(RECORDS_KEY, JSON.stringify(records));
  } catch {}
}

function formatDate(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '未知时间';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getMonth() + 1}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function getRecordSummary(record: ConsultationRecord) {
  const userMessages = record.messages?.filter(msg => msg.role === 'user') || [];
  const assistantMessages = record.messages?.filter(msg => msg.role === 'assistant') || [];
  const lastUser = [...userMessages].reverse()[0]?.content;
  const profile = record.userProfile || {};
  const profileText = [
    profile.province,
    profile.subjects?.join('+'),
    profile.score ? `${profile.score}分` : undefined,
    profile.rank ? `位次${profile.rank}` : undefined,
  ].filter(Boolean).join(' · ');

  return {
    messageCount: (record.messages || []).length,
    userCount: userMessages.length,
    assistantCount: assistantMessages.length,
    lastUser,
    profileText,
    hasPlan: Boolean(record.currentPlan),
    hasAudit: Boolean(record.currentAuditReport),
  };
}

export default function ConsultationsPage() {
  const router = useRouter();
  const [records, setRecords] = useState<ConsultationRecord[]>([]);
  const [keyword, setKeyword] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<ConsultationRecord | null>(null);

  useEffect(() => {
    setRecords(loadRecords());
  }, []);

  const filteredRecords = useMemo(() => {
    const q = keyword.trim().toLowerCase();
    if (!q) return records;
    return records.filter(record => {
      const text = [
        record.title,
        record.userProfile?.province,
        record.userProfile?.score,
        record.userProfile?.rank,
        record.userProfile?.subjects?.join(' '),
        ...(record.messages || []).map(msg => msg.content),
      ].filter(Boolean).join(' ').toLowerCase();
      return text.includes(q);
    });
  }, [records, keyword]);

  const openRecord = (id: string) => {
    try {
      localStorage.setItem(ACTIVE_KEY, id);
    } catch {}
    router.push('/');
  };

  const startNewConsultation = () => {
    try {
      localStorage.removeItem(ACTIVE_KEY);
    } catch {}
    router.push('/?new=1');
  };

  const confirmDelete = () => {
    if (!deleteTarget) return;
    const updated = records.filter(record => record.id !== deleteTarget.id);
    saveRecords(updated);
    setRecords(updated);
    try {
      if (localStorage.getItem(ACTIVE_KEY) === deleteTarget.id) {
        localStorage.removeItem(ACTIVE_KEY);
      }
    } catch {}
    setDeleteTarget(null);
  };

  return (
    <div className="flex flex-col min-h-screen max-w-3xl mx-auto bg-white shadow-lg">
      <header className="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-white/95 backdrop-blur sticky top-0 z-10">
        <Link href="/" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>返回对话</span>
        </Link>
        <div className="text-center">
          <h1 className="text-sm font-bold text-gray-800">咨询记录</h1>
          <p className="text-[11px] text-gray-400">恢复历史对话与规划上下文</p>
        </div>
        <button
          onClick={startNewConsultation}
          className="text-xs px-3 py-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
        >
          新建咨询
        </button>
      </header>

      <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
        <div className="relative">
          <input
            value={keyword}
            onChange={e => setKeyword(e.target.value)}
            placeholder="搜索记录：分数、省份、职业、方案关键词..."
            className="w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          {keyword && (
            <button
              onClick={() => setKeyword('')}
              className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          )}
        </div>
      </div>

      {records.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center px-6 py-16 text-center">
          <div className="w-28 h-28 bg-blue-50 rounded-full flex items-center justify-center mb-6 text-4xl">💬</div>
          <h2 className="text-base font-semibold text-gray-800 mb-2">暂无咨询记录</h2>
          <p className="text-sm text-gray-500 leading-relaxed mb-6">
            你和升学助手的每次咨询会自动保存。生成方案、职业解读、审核结果都能在这里回溯。
          </p>
          <button
            onClick={startNewConsultation}
            className="px-6 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            开始第一次咨询
          </button>
        </div>
      ) : filteredRecords.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center px-6 py-16 text-center">
          <div className="text-4xl mb-4">🔎</div>
          <p className="text-sm text-gray-500">没有找到匹配的咨询记录</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {filteredRecords.map(record => {
            const summary = getRecordSummary(record);
            return (
              <div key={record.id} className="border border-gray-200 rounded-2xl bg-white shadow-sm overflow-hidden">
                <button
                  onClick={() => openRecord(record.id)}
                  className="w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-semibold text-gray-800 truncate">{record.title || '未命名咨询'}</h3>
                      <p className="text-xs text-gray-400 mt-1">
                        更新于 {formatDate(record.updatedAt)} · {summary.messageCount} 条消息
                      </p>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      {summary.hasPlan && <span className="text-[11px] px-2 py-1 rounded-full bg-green-50 text-green-700">有方案</span>}
                      {summary.hasAudit && <span className="text-[11px] px-2 py-1 rounded-full bg-orange-50 text-orange-700">已审核</span>}
                    </div>
                  </div>
                  {summary.profileText && (
                    <p className="mt-2 text-xs text-blue-700 bg-blue-50 inline-flex px-2 py-1 rounded-full">
                      {summary.profileText}
                    </p>
                  )}
                  {summary.lastUser && (
                    <p className="mt-2 text-xs text-gray-500 line-clamp-2">
                      最近提问：{summary.lastUser}
                    </p>
                  )}
                </button>
                <div className="px-4 py-2 border-t border-gray-100 bg-gray-50 flex items-center justify-between">
                  <div className="text-[11px] text-gray-400">
                    用户 {summary.userCount} 轮 · AI {summary.assistantCount} 轮
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => openRecord(record.id)}
                      className="text-xs px-3 py-1.5 rounded-lg bg-white border border-gray-200 text-gray-600 hover:text-blue-600 hover:border-blue-200 transition-colors"
                    >
                      恢复对话
                    </button>
                    <button
                      onClick={() => setDeleteTarget(record)}
                      className="text-xs px-3 py-1.5 rounded-lg bg-white border border-gray-200 text-gray-500 hover:text-red-600 hover:border-red-200 transition-colors"
                    >
                      删除
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {deleteTarget && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 px-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-sm w-full p-5">
            <h3 className="text-base font-semibold text-gray-800 mb-2">删除咨询记录？</h3>
            <p className="text-sm text-gray-500 leading-relaxed mb-5">
              将删除“{deleteTarget.title || '未命名咨询'}”及其中的对话上下文。已单独保存的志愿方案不会删除。
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setDeleteTarget(null)}
                className="px-4 py-2 text-sm rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={confirmDelete}
                className="px-4 py-2 text-sm rounded-lg bg-red-600 text-white hover:bg-red-700"
              >
                确认删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
