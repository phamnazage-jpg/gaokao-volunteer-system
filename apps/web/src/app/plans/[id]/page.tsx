'use client';

import React, { useState, useEffect, useMemo, use } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import type { SavedPlan } from '@/lib/useChat';

interface School {
  university: string;
  major: string;
  estScore: number;
  probability: number;
  risk: string;
  riskType: string;
  reason: string;
}

const TABS = [
  { key: 'rush', label: '🚀 冲刺', color: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200', bar: 'bg-orange-500' },
  { key: 'stable', label: '✅ 稳妥', color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200', bar: 'bg-blue-500' },
  { key: 'safe', label: '🛡️ 保底', color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200', bar: 'bg-green-500' },
];

function getProbColor(p: number): string {
  if (p >= 80) return 'bg-green-500';
  if (p >= 50) return 'bg-blue-500';
  if (p >= 30) return 'bg-yellow-500';
  return 'bg-orange-500';
}

function getRiskBadge(risk: string) {
  if (risk === '低') return 'bg-green-100 text-green-700';
  if (risk === '中') return 'bg-yellow-100 text-yellow-700';
  return 'bg-red-100 text-red-700';
}

export default function PlanDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const searchParams = useSearchParams();
  const action = searchParams.get('action');
  const [plan, setPlan] = useState<SavedPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('stable');
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [expandedSchool, setExpandedSchool] = useState<string | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem('savedPlans');
      const all: SavedPlan[] = raw ? JSON.parse(raw) : [];
      setPlan(all.find(p => p.id === id) || null);
    } catch {
    } finally {
      setLoading(false);
    }
  }, [id]);

  // Auto open export menu if ?action=export
  useEffect(() => {
    if (action === 'export' && plan) {
      setShowExportMenu(true);
    }
  }, [action, plan]);

  const currentList: School[] = useMemo(() => {
    if (!plan) return [];
    return plan.plan[activeTab as keyof typeof plan.plan] || [];
  }, [plan, activeTab]);

  const tab = TABS.find(t => t.key === activeTab)!;

  const riskStats = useMemo(() => {
    if (!plan) return { high: 0, medium: 0, low: 0 };
    const all: School[] = [
      ...(plan.plan.rush || []),
      ...(plan.plan.stable || []),
      ...(plan.plan.safe || []),
    ];
    return {
      high: all.filter(s => s.risk === '较高' || s.risk === '高').length,
      medium: all.filter(s => s.risk === '中').length,
      low: all.filter(s => s.risk === '低').length,
    };
  }, [plan]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-400 text-sm">加载中...</p>
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="flex flex-col min-h-screen max-w-3xl mx-auto bg-white shadow-lg">
        <header className="flex items-center px-4 py-3 border-b border-gray-100">
          <Link href="/plans" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span>返回</span>
          </Link>
        </header>
        <div className="flex-1 flex items-center justify-center">
          <p className="text-gray-400 text-sm">方案不存在或已被删除</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen max-w-3xl mx-auto bg-white shadow-lg">
      {/* Header */}
      <header className="flex items-center px-4 py-3 border-b border-gray-100 bg-white/95 backdrop-blur sticky top-0 z-10">
        <Link href="/plans" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors flex-shrink-0">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>返回</span>
        </Link>
        <h1 className="flex-1 text-center text-sm font-bold text-gray-800 truncate px-2">{plan.name}</h1>
        <div className="flex items-center gap-1 flex-shrink-0 relative">
          <button
            onClick={() => setShowExportMenu(!showExportMenu)}
            className="px-2.5 py-1.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            导出
          </button>
          <Link
            href="/"
            className="px-2.5 py-1.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            编辑
          </Link>

          {/* Export dropdown */}
          {showExportMenu && (
            <div className="absolute top-full right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 py-1 min-w-[120px]">
              <button
                onClick={() => {
                  setShowExportMenu(false);
                  alert('导出图片功能：将方案保存为长图');
                }}
                className="w-full text-left px-3 py-2 text-xs text-gray-600 hover:bg-gray-50 transition-colors"
              >
                📷 导出图片
              </button>
              <button
                onClick={() => {
                  setShowExportMenu(false);
                  alert('导出PDF功能：将方案保存为PDF文件');
                }}
                className="w-full text-left px-3 py-2 text-xs text-gray-600 hover:bg-gray-50 transition-colors"
              >
                📄 导出PDF
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Close export menu on outside click */}
      {showExportMenu && (
        <div className="fixed inset-0 z-10" onClick={() => setShowExportMenu(false)} />
      )}

      <div className="flex-1 overflow-y-auto">
        {/* User info bar */}
        <div className="px-4 py-3 bg-gradient-to-r from-blue-50 to-purple-50 border-b border-gray-100">
          <div className="flex items-center gap-3 text-xs text-gray-600 flex-wrap">
            <span className="flex items-center gap-1">
              <span className="text-gray-400">📍</span>
              {plan.profile.province || '—'}
            </span>
            <span className="text-gray-300">|</span>
            <span className="flex items-center gap-1">
              <span className="text-gray-400">📚</span>
              {plan.profile.subjects?.join('+') || '—'}
            </span>
            <span className="text-gray-300">|</span>
            <span className="flex items-center gap-1">
              <span className="text-gray-400">📊</span>
              {plan.profile.score || '—'}分
            </span>
            <span className="text-gray-300">|</span>
            <span className="flex items-center gap-1">
              <span className="text-gray-400">🏅</span>
              位次{plan.profile.rank || '—'}
            </span>
          </div>
        </div>

        {/* Preferences bar */}
        {plan.profile.preferences && (
          <div className="px-4 py-2 bg-gray-50 border-b border-gray-100">
            <div className="flex items-center gap-3 text-xs text-gray-500 flex-wrap">
              {plan.profile.preferences.region && plan.profile.preferences.region.length > 0 && (
                <span>地域偏好：{plan.profile.preferences.region.join('、')}</span>
              )}
              {plan.profile.preferences.majorDirection && plan.profile.preferences.majorDirection.length > 0 && (
                <span>专业方向：{plan.profile.preferences.majorDirection.join('、')}</span>
              )}
              {plan.profile.preferences.tuition && (
                <span>学费：{plan.profile.preferences.tuition}</span>
              )}
              {plan.profile.preferences.careerPlan && (
                <span>规划：{plan.profile.preferences.careerPlan}</span>
              )}
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex border-b border-gray-100">
          {TABS.map(t => (
            <button
              key={t.key}
              onClick={() => { setActiveTab(t.key); setExpandedSchool(null); }}
              className={`flex-1 py-3 text-xs font-medium transition-colors relative ${
                activeTab === t.key ? t.color : 'text-gray-400 hover:text-gray-600'
              }`}
            >
              {t.label}
              <span className="ml-1 text-gray-400">({plan.plan[t.key as keyof typeof plan.plan]?.length || 0}所)</span>
              {activeTab === t.key && (
                <div className={`absolute bottom-0 left-4 right-4 h-0.5 ${t.bar}`} />
              )}
            </button>
          ))}
        </div>

        {/* School List */}
        <div className="divide-y divide-gray-50">
          {currentList.map((school, idx) => (
            <div key={`${school.university}-${idx}`}>
              <div
                onClick={() => setExpandedSchool(expandedSchool === `${activeTab}-${idx}` ? null : `${activeTab}-${idx}`)}
                className="px-4 py-3 hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-400 w-5">{idx + 1}</span>
                      <span className="text-sm font-medium text-gray-800 truncate">{school.university}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded ${getRiskBadge(school.risk)}`}>
                        {school.risk}风险
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5 ml-7">{school.major}</div>
                  </div>
                  <div className="flex items-center gap-3 ml-3 flex-shrink-0">
                    <div className="text-right">
                      <div className="text-sm font-semibold text-gray-800">预估{school.estScore}分</div>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${getProbColor(school.probability)}`}
                            style={{ width: `${school.probability}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500 w-8">{school.probability}%</span>
                      </div>
                    </div>
                    <svg
                      className={`w-4 h-4 text-gray-300 transition-transform flex-shrink-0 ${expandedSchool === `${activeTab}-${idx}` ? 'rotate-180' : ''}`}
                      fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>
              {expandedSchool === `${activeTab}-${idx}` && (
                <div className="px-4 pb-3 ml-7">
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-600">{school.reason}</p>
                    {school.riskType !== '—' && (
                      <p className="text-xs text-red-600 mt-1">⚠️ {school.riskType}</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Risk warning */}
        <div className="px-4 py-4 space-y-2">
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
            <h4 className="text-xs font-semibold text-yellow-800 mb-2">⚠️ 风险提示</h4>
            <ul className="text-xs text-yellow-700 space-y-1">
              {riskStats.high > 0 && (
                <li>• 当前方案中有 {riskStats.high} 所院校存在较高风险，建议关注录取位次波动</li>
              )}
              {riskStats.medium > 0 && (
                <li>• {riskStats.medium} 所院校存在中等风险，建议参考近3年数据综合判断</li>
              )}
              <li>• 院校录取位次每年波动，本方案仅供参考</li>
              <li>• 请务必查阅省教育考试院官方招生计划</li>
            </ul>
          </div>
          <p className="text-xs text-gray-400 text-center">
            数据来源：广东省教育考试院历年录取数据 | AI辅助决策，请以官方信息为准
          </p>
        </div>
      </div>
    </div>
  );
}
