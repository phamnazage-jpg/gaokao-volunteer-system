'use client';

import React, { Suspense, useState, useEffect, useMemo } from 'react';
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

function getProbColor(p: number): string {
  if (p >= 80) return 'bg-green-500';
  if (p >= 50) return 'bg-blue-500';
  if (p >= 30) return 'bg-yellow-500';
  return 'bg-orange-500';
}

function CompareContent() {
  const searchParams = useSearchParams();
  const idsParam = searchParams.get('ids') || '';
  const ids = idsParam.split(',').filter(Boolean);

  const [plans, setPlans] = useState<SavedPlan[]>([]);
  const [planA, setPlanA] = useState<SavedPlan | null>(null);
  const [planB, setPlanB] = useState<SavedPlan | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      const raw = localStorage.getItem('savedPlans');
      const all: SavedPlan[] = raw ? JSON.parse(raw) : [];
      setPlans(all);
      if (ids.length >= 1) setPlanA(all.find(p => p.id === ids[0]) || null);
      if (ids.length >= 2) setPlanB(all.find(p => p.id === ids[1]) || null);
    } catch {
    } finally {
      setLoading(false);
    }
  }, [idsParam]);

  const getSchools = (plan: any): School[] => {
    if (!plan) return [];
    return [...(plan.rush || []), ...(plan.stable || []), ...(plan.safe || [])];
  };

  const schoolsA = useMemo(() => getSchools(planA?.plan), [planA]);
  const schoolsB = useMemo(() => getSchools(planB?.plan), [planB]);

  const countByCategory = (plan: any) => ({
    rush: plan?.rush?.length || 0,
    stable: plan?.stable?.length || 0,
    safe: plan?.safe?.length || 0,
  });

  const totalA = schoolsA.length;
  const totalB = schoolsB.length;
  const catA = countByCategory(planA?.plan);
  const catB = countByCategory(planB?.plan);

  const regionsA = useMemo(() => {
    const set = new Set<string>();
    schoolsA.forEach(s => {
      const m = s.university.match(/^(.+?)(大学|学院)/);
      if (m) set.add(m[0]);
    });
    return set.size;
  }, [schoolsA]);

  const regionsB = useMemo(() => {
    const set = new Set<string>();
    schoolsB.forEach(s => {
      const m = s.university.match(/^(.+?)(大学|学院)/);
      if (m) set.add(m[0]);
    });
    return set.size;
  }, [schoolsB]);

  const diffSet = useMemo(() => {
    const namesA = new Set(schoolsA.map(s => s.university + s.major));
    const namesB = new Set(schoolsB.map(s => s.university + s.major));
    const diff = new Set<string>();
    schoolsA.forEach(s => {
      if (!namesB.has(s.university + s.major)) diff.add(s.university + s.major);
    });
    schoolsB.forEach(s => {
      if (!namesA.has(s.university + s.major)) diff.add(s.university + s.major);
    });
    return diff;
  }, [schoolsA, schoolsB]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-400 text-sm">加载中...</p>
      </div>
    );
  }

  if (!planA || !planB) {
    return (
      <div className="flex flex-col min-h-screen max-w-3xl mx-auto bg-white shadow-lg">
        <header className="flex items-center px-4 py-3 border-b border-gray-100">
          <Link href="/plans" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span>返回</span>
          </Link>
          <h1 className="flex-1 text-center text-sm font-bold text-gray-800 -ml-8">方案对比</h1>
        </header>
        <div className="flex-1 flex items-center justify-center">
          <p className="text-gray-400 text-sm">方案数据不完整，请返回重新选择</p>
        </div>
      </div>
    );
  }

  const formatPercent = (count: number, total: number) => {
    if (total === 0) return '0%';
    return Math.round((count / total) * 100) + '%';
  };

  return (
    <div className="flex flex-col min-h-screen max-w-3xl mx-auto bg-white shadow-lg">
      {/* Header */}
      <header className="flex items-center px-4 py-3 border-b border-gray-100 bg-white/95 backdrop-blur sticky top-0 z-10">
        <Link href="/plans" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>返回</span>
        </Link>
        <h1 className="flex-1 text-center text-sm font-bold text-gray-800 -ml-8">方案对比</h1>
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {/* Comparison table */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 w-24">对比维度</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-blue-600">{planA.name}</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-orange-600">{planB.name}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                <tr>
                  <td className="px-4 py-3 text-xs text-gray-500">院校总数</td>
                  <td className="px-4 py-3 text-center text-sm font-semibold text-gray-800">{totalA}所</td>
                  <td className="px-4 py-3 text-center text-sm font-semibold text-gray-800">{totalB}所</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-xs text-gray-500">🚀 冲刺</td>
                  <td className="px-4 py-3 text-center text-xs text-gray-700">
                    {catA.rush}所 <span className="text-gray-400">({formatPercent(catA.rush, totalA)})</span>
                  </td>
                  <td className="px-4 py-3 text-center text-xs text-gray-700">
                    {catB.rush}所 <span className="text-gray-400">({formatPercent(catB.rush, totalB)})</span>
                  </td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-xs text-gray-500">✅ 稳妥</td>
                  <td className="px-4 py-3 text-center text-xs text-gray-700">
                    {catA.stable}所 <span className="text-gray-400">({formatPercent(catA.stable, totalA)})</span>
                  </td>
                  <td className="px-4 py-3 text-center text-xs text-gray-700">
                    {catB.stable}所 <span className="text-gray-400">({formatPercent(catB.stable, totalB)})</span>
                  </td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-xs text-gray-500">🛡️ 保底</td>
                  <td className="px-4 py-3 text-center text-xs text-gray-700">
                    {catA.safe}所 <span className="text-gray-400">({formatPercent(catA.safe, totalA)})</span>
                  </td>
                  <td className="px-4 py-3 text-center text-xs text-gray-700">
                    {catB.safe}所 <span className="text-gray-400">({formatPercent(catB.safe, totalB)})</span>
                  </td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-xs text-gray-500">地域覆盖</td>
                  <td className="px-4 py-3 text-center text-xs text-gray-700">{regionsA}所院校</td>
                  <td className="px-4 py-3 text-center text-xs text-gray-700">{regionsB}所院校</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Side by side school lists */}
        <div>
          <h3 className="text-sm font-semibold text-gray-800 mb-3">
            📋 院校列表对比 <span className="text-xs font-normal text-gray-400 ml-1">(黄色背景 = 差异院校)</span>
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {/* Plan A */}
            <div>
              <h4 className="text-xs font-semibold text-blue-600 mb-2">{planA.name}</h4>
              <div className="space-y-1.5">
                {schoolsA.map((school, idx) => {
                  const isDiff = diffSet.has(school.university + school.major);
                  return (
                    <div
                      key={idx}
                      className={`px-3 py-2 rounded-lg text-xs border ${
                        isDiff ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50 border-gray-100'
                      }`}
                    >
                      <div className="font-medium text-gray-800">{school.university}</div>
                      <div className="text-gray-500">{school.major}</div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-gray-700 font-medium">预估{school.estScore}分</span>
                        <div className="flex-1 h-1 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${getProbColor(school.probability)}`}
                            style={{ width: `${school.probability}%` }}
                          />
                        </div>
                        <span className="text-gray-400">{school.probability}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Plan B */}
            <div>
              <h4 className="text-xs font-semibold text-orange-600 mb-2">{planB.name}</h4>
              <div className="space-y-1.5">
                {schoolsB.map((school, idx) => {
                  const isDiff = diffSet.has(school.university + school.major);
                  return (
                    <div
                      key={idx}
                      className={`px-3 py-2 rounded-lg text-xs border ${
                        isDiff ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50 border-gray-100'
                      }`}
                    >
                      <div className="font-medium text-gray-800">{school.university}</div>
                      <div className="text-gray-500">{school.major}</div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-gray-700 font-medium">预估{school.estScore}分</span>
                        <div className="flex-1 h-1 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${getProbColor(school.probability)}`}
                            style={{ width: `${school.probability}%` }}
                          />
                        </div>
                        <span className="text-gray-400">{school.probability}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ComparePage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><div className="text-gray-500">加载中...</div></div>}>
      <CompareContent />
    </Suspense>
  );
}
