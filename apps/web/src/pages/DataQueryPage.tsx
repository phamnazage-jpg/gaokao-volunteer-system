/**
 * V10 · Sprint 3 · DataQueryPage
 * 数据查询页：分数线 / 位次 / 专业 / 院校
 */
import { useState } from 'react';
import { Database, TrendingUp, GraduationCap } from 'lucide-react';
import { useScoreLineQuery, useRankEstimatorQuery, useMajorsQuery, useSchoolsQuery } from '@/hooks/useDataQuery';

export function DataQueryPage() {
  const [province, setProvince] = useState('广东');
  const [year, setYear] = useState(2025);
  const [scoreType, setScoreType] = useState<'physics' | 'history'>('physics');
  const [rank, setRank] = useState(12500);
  const [keyword, setKeyword] = useState('');

  const scoreLine = useScoreLineQuery({ province, year, scoreType });
  const rankEst = useRankEstimatorQuery({ province, year, scoreType, rank });
  const majors = useMajorsQuery(keyword);
  const schools = useSchoolsQuery(keyword);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
        <Database className="w-6 h-6" aria-hidden="true" />
        数据查询
      </h1>

      <div className="mt-6 grid gap-4 md:grid-cols-4">
        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">省份</span>
          <input
            type="text"
            value={province}
            onChange={(e) => setProvince(e.target.value)}
            className="px-3 py-2 rounded-lg border border-gray-200 text-sm min-h-[48px]"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">年份</span>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="px-3 py-2 rounded-lg border border-gray-200 text-sm min-h-[48px]"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">科类</span>
          <select
            value={scoreType}
            onChange={(e) => setScoreType(e.target.value as 'physics' | 'history')}
            className="px-3 py-2 rounded-lg border border-gray-200 text-sm min-h-[48px]"
          >
            <option value="physics">物理</option>
            <option value="history">历史</option>
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">位次</span>
          <input
            type="number"
            value={rank}
            onChange={(e) => setRank(Number(e.target.value))}
            className="px-3 py-2 rounded-lg border border-gray-200 text-sm min-h-[48px]"
          />
        </label>
      </div>

      {rankEst.data && (
        <div className="mt-6 rounded-xl border border-gray-100 bg-white p-4 shadow-sm flex items-center gap-3">
          <TrendingUp className="w-8 h-8 text-blue-500" aria-hidden="true" />
          <div>
            <p className="text-xs text-gray-400">等效分数</p>
            <p className="text-2xl font-bold text-gray-800">{rankEst.data.equivalentScore}</p>
          </div>
        </div>
      )}

      {scoreLine.data && (
        <div className="mt-6 rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold text-gray-400 mb-2">分数线（{scoreLine.data.year}）</p>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-400 border-b">
                <th className="text-left py-2">批次</th>
                <th className="text-right py-2">分数</th>
                <th className="text-right py-2">位次</th>
              </tr>
            </thead>
            <tbody>
              {scoreLine.data.lines.map((line) => (
                <tr key={line.batch} className="border-b last:border-0">
                  <td className="py-2 text-gray-800">{line.batch}</td>
                  <td className="py-2 text-right text-gray-800">{line.score}</td>
                  <td className="py-2 text-right text-gray-500">{line.rank.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-6">
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="搜索专业或院校…"
          className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm min-h-[48px]"
        />
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold text-gray-400 mb-2 flex items-center gap-1">
            <GraduationCap className="w-4 h-4" /> 专业
          </p>
          <ul className="text-sm space-y-1">
            {(majors.data?.majors ?? []).slice(0, 8).map((m) => (
              <li key={m.id} className="text-gray-700">
                {m.name} <span className="text-xs text-gray-400">· {m.category}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold text-gray-400 mb-2">院校</p>
          <ul className="text-sm space-y-1">
            {(schools.data?.schools ?? []).slice(0, 8).map((s) => (
              <li key={s.id} className="text-gray-700">
                {s.name} <span className="text-xs text-gray-400">· {s.province}</span>
                {s.is985 && <span className="ml-1 text-xs text-red-500">985</span>}
                {s.is211 && <span className="ml-1 text-xs text-orange-500">211</span>}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}