'use client';

import React, { useState } from 'react';

interface Props {
  data: {
    missingFields: string[];
    currentProfile: Record<string, any>;
  };
  onSubmit: (data: Record<string, any>) => void;
}

type StepKey = 'basic' | 'subjects' | 'prefs';

export function FormCard({ data, onSubmit }: Props) {
  const [province, setProvince] = useState(data.currentProfile.province || '');
  const [score, setScore] = useState(data.currentProfile.score?.toString() || '');
  const [rank, setRank] = useState(data.currentProfile.rank?.toString() || '');
  const [examType, setExamType] = useState<'physics' | 'history' | ''>(data.currentProfile.subjects?.[0] === '物理' ? 'physics' : data.currentProfile.subjects?.[0] === '历史' ? 'history' : '');
  const [chem, setChem] = useState(data.currentProfile.subjects?.includes('化学') || false);
  const [bio, setBio] = useState(data.currentProfile.subjects?.includes('生物') || false);
  const [politics, setPolitics] = useState(data.currentProfile.subjects?.includes('政治') || false);
  const [geo, setGeo] = useState(data.currentProfile.subjects?.includes('地理') || false);
  const [region, setRegion] = useState('');
  const [majorDir, setMajorDir] = useState('');

  // 字段触碰状态——仅交互后才显示验证提示
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [currentStep, setCurrentStep] = useState<StepKey>('basic');

  const markTouched = (field: string) => setTouched(prev => ({ ...prev, [field]: true }));

  // === 字段验证 ===
  const scoreNum = parseInt(score);
  const scoreError = touched.score && score
    ? (Number.isNaN(scoreNum) || scoreNum < 0 || scoreNum > 750 ? '分数应在 0~750 之间' : '')
    : '';
  const rankError = touched.rank && rank
    ? (Number.isNaN(parseInt(rank)) || parseInt(rank) < 1 ? '请输入有效的位次' : '')
    : '';

  // === 必填校验 ===
  const basicComplete = Boolean(province && score && !scoreError && rank && !rankError);
  const subjectsComplete = Boolean(examType && (chem || bio || politics || geo));
  const canSubmit = basicComplete && subjectsComplete;

  // === 步骤进度 ===
  const steps: { key: StepKey; label: string; complete: boolean; active: boolean }[] = [
    { key: 'basic', label: '基本信息', complete: basicComplete, active: currentStep === 'basic' },
    { key: 'subjects', label: '选科组合', complete: subjectsComplete, active: currentStep === 'subjects' },
    { key: 'prefs', label: '偏好设置', complete: canSubmit, active: currentStep === 'prefs' },
  ];

  const completedCount = steps.filter(s => s.complete).length;

  const handleSubmit = () => {
    if (!canSubmit) return;
    const subjects = [examType === 'physics' ? '物理' : '历史'];
    if (examType === 'physics') { if (chem) subjects.push('化学'); if (bio) subjects.push('生物'); if (politics) subjects.push('政治'); if (geo) subjects.push('地理'); }
    else { if (politics) subjects.push('政治'); if (geo) subjects.push('地理'); if (chem) subjects.push('化学'); if (bio) subjects.push('生物'); }

    onSubmit({
      province,
      score: parseInt(score),
      rank: parseInt(rank),
      subjects,
      preferences: {
        region: region ? [region] : [],
        majorDirection: majorDir ? [majorDir] : [],
      },
    });
  };

  const goToStep = (step: StepKey) => {
    // 不允许跳过未完成步骤
    if (step === 'subjects' && !basicComplete) return;
    if (step === 'prefs' && !subjectsComplete) return;
    setCurrentStep(step);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-md shadow-sm p-5 space-y-4">
      {/* 对话式引导提示 — 用户可以直接对话而无需填表 */}
      <div className="bg-blue-50/50 rounded-lg px-3 py-2 border border-blue-100">
        <p className="text-xs text-blue-700">
          💬 <span className="font-medium">更喜欢直接聊？</span> 你也可以在对话框里说「广东物理620分」，系统会自动识别你的信息～
        </p>
      </div>

      {/* 标题 + 进度指示器 */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-800" id="form-title">📋 完善你的信息</h3>
          <span className="text-xs text-gray-400" aria-live="polite">{completedCount}/{steps.length} 步骤完成</span>
        </div>

        {/* 步骤点 */}
        <div className="flex items-center gap-1 mb-1">
          {steps.map((step, idx) => (
            <React.Fragment key={step.key}>
              <button
                onClick={() => goToStep(step.key)}
                disabled={step.complete ? false : !steps.slice(0, idx).every(s => s.complete)}
                className={`group flex items-center gap-1.5 px-2 py-1 rounded-md text-xs transition-colors ${
                  step.active
                    ? 'bg-blue-50 text-blue-700 font-medium'
                    : step.complete
                    ? 'bg-green-50 text-green-600 cursor-pointer hover:bg-green-100'
                    : 'text-gray-400 cursor-not-allowed'
                }`}
                title={step.label}
              >
                <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${
                  step.active ? 'bg-blue-600 text-white' : step.complete ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-500'
                }`}>
                  {step.complete ? '✓' : idx + 1}
                </span>
                <span className="hidden sm:inline">{step.label}</span>
              </button>
              {idx < steps.length - 1 && (
                <div className={`flex-1 h-px mx-0.5 ${step.complete ? 'bg-green-300' : 'bg-gray-200'}`} />
              )}
            </React.Fragment>
          ))}
        </div>
        <p className="text-xs text-gray-400 mt-2">
          {currentStep === 'basic' && '第一步：填写省份、分数和位次'}
          {currentStep === 'subjects' && '第二步：选择你的高考选科组合'}
          {currentStep === 'prefs' && (canSubmit ? '🎉 信息齐全！可跳过偏好直接生成方案' : '还需完成基本信息')}
        </p>
      </div>

      {/* === 步骤 1：基本信息 === */}
      {currentStep === 'basic' && (
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1.5">
              省份 <span className="text-red-400">*</span>
            </label>
            <select
              value={province}
              onChange={e => { setProvince(e.target.value); markTouched('province'); }}
              aria-label="选择高考省份"
              aria-required="true"
              aria-describedby={touched.province && !province ? 'province-error' : undefined}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                touched.province && !province ? 'border-red-300 bg-red-50' : 'border-gray-200'
              }`}
            >
              <option value="">请选择高考省份</option>
              {['广东','北京','上海','天津','重庆','江苏','浙江','山东','河南','四川','湖北','湖南','福建','安徽','河北','辽宁','吉林','黑龙江','陕西','山西','江西','广西','云南','贵州','海南','甘肃','宁夏','青海','西藏','新疆','内蒙古'].map(p => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1.5">
              高考分数 <span className="text-red-400">*</span>
            </label>
            <input
              type="number"
              value={score}
              onChange={e => { setScore(e.target.value); markTouched('score'); }}
              onBlur={() => markTouched('score')}
              placeholder="如 620"
              min={0}
              max={750}
              aria-label="高考分数"
              aria-required="true"
              aria-describedby={scoreError ? 'score-error' : undefined}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                scoreError ? 'border-red-300 bg-red-50' : 'border-gray-200'
              }`}
            />
            {scoreError && <p className="text-xs text-red-500 mt-1" id="score-error" role="alert">{scoreError}</p>}
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1.5">
              全省位次 <span className="text-red-400">*</span>
              <span className="text-gray-400 font-normal ml-1">（成绩单上的排名）</span>
            </label>
            <input
              type="number"
              value={rank}
              onChange={e => { setRank(e.target.value); markTouched('rank'); }}
              onBlur={() => markTouched('rank')}
              placeholder="如 8500"
              aria-label="全省位次排名"
              aria-required="true"
              aria-describedby={rankError ? 'rank-error' : undefined}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                rankError ? 'border-red-300 bg-red-50' : 'border-gray-200'
              }`}
            />
            {rankError && <p className="text-xs text-red-500 mt-1" id="rank-error" role="alert">{rankError}</p>}
          </div>

          <button
            onClick={() => { markTouched('province'); markTouched('score'); markTouched('rank'); goToStep('subjects'); }}
            disabled={!basicComplete}
            className={`w-full py-2 rounded-lg text-sm font-medium transition-all ${
              basicComplete
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            下一步：选科 →
          </button>
        </div>
      )}

      {/* === 步骤 2：选科组合 === */}
      {currentStep === 'subjects' && (
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-2">
              首选科目 <span className="text-red-400">*</span>
            </label>
            <div className="flex gap-2">
              {(['physics', 'history'] as const).map(type => (
                <button
                  key={type}
                  onClick={() => { setExamType(type); markTouched('examType'); }}
                  className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    examType === type ? 'bg-blue-600 text-white shadow-sm' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {type === 'physics' ? '物理' : '历史'}
                </button>
              ))}
            </div>
          </div>

          {examType && (
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-2">
                再选科目 <span className="text-red-400">*</span>
                <span className="text-gray-400 font-normal ml-1">（至少选2门）</span>
              </label>
              <div className="flex flex-wrap gap-2">
                {(examType === 'physics'
                  ? [{ key: 'chem', label: '化学', value: chem, setter: setChem }, { key: 'bio', label: '生物', value: bio, setter: setBio }, { key: 'politics', label: '政治', value: politics, setter: setPolitics }, { key: 'geo', label: '地理', value: geo, setter: setGeo }]
                  : [{ key: 'politics', label: '政治', value: politics, setter: setPolitics }, { key: 'geo', label: '地理', value: geo, setter: setGeo }, { key: 'chem', label: '化学', value: chem, setter: setChem }, { key: 'bio', label: '生物', value: bio, setter: setBio }]
                ).map(({ key, label, value, setter }) => (
                  <button
                    key={key}
                    onClick={() => { setter(!value); markTouched(key); }}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      value ? 'bg-green-100 text-green-700 border border-green-300' : 'bg-gray-50 text-gray-500 border border-gray-200 hover:bg-gray-100'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
              {touched.examType && !subjectsComplete && (
                <p className="text-xs text-amber-600 mt-1.5">请至少选择 2 门再选科目</p>
              )}
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={() => setCurrentStep('basic')}
              className="flex-1 py-2 rounded-lg text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 transition-colors"
            >
              ← 返回
            </button>
            <button
              onClick={() => { markTouched('examType'); goToStep('prefs'); }}
              disabled={!subjectsComplete}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                subjectsComplete
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              }`}
            >
              下一步：偏好设置 →
            </button>
          </div>
        </div>
      )}

      {/* === 步骤 3：偏好设置 + 提交 === */}
      {currentStep === 'prefs' && (
        <div className="space-y-4">
          {/* 偏好（可选） */}
          <div className="bg-gray-50 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-medium text-gray-600">⚙️ 个性化偏好（选填）</p>
              <button
                onClick={handleSubmit}
                disabled={!canSubmit}
                className={`text-xs underline transition-colors ${
                  canSubmit ? 'text-blue-600 hover:text-blue-700' : 'text-gray-400 cursor-not-allowed'
                }`}
              >
                跳过，直接用默认偏好生成 →
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">地域偏好</label>
                <select
                  value={region}
                  onChange={e => setRegion(e.target.value)}
                  className="w-full bg-white border border-gray-200 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">不限</option>
                  <option value="珠三角">珠三角</option>
                  <option value="长三角">长三角</option>
                  <option value="京津冀">京津冀</option>
                  <option value="川渝">川渝</option>
                  <option value="华中">华中</option>
                  <option value="西北">西北</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">专业方向</label>
                <select
                  value={majorDir}
                  onChange={e => setMajorDir(e.target.value)}
                  className="w-full bg-white border border-gray-200 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">不限</option>
                  <option value="计算机/电子">计算机/电子</option>
                  <option value="医学">医学</option>
                  <option value="经管">经管</option>
                  <option value="文史哲">文史哲</option>
                  <option value="法学">法学</option>
                  <option value="师范">师范</option>
                </select>
              </div>
            </div>
          </div>

          {/* 已确认的信息摘要 */}
          {canSubmit && (
            <div className="bg-blue-50 rounded-xl p-3 text-xs text-blue-800 space-y-1">
              <p className="font-medium mb-1">即将基于以下信息生成方案：</p>
              <p>📍 {province} · 🎯 {score}分 · 🏅 位次{rank}</p>
              <p>📚 {examType === 'physics' ? '物理' : '历史'}类 · {
                [chem && '化学', bio && '生物', politics && '政治', geo && '地理'].filter(Boolean).join('+') || '未选'
              }</p>
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={() => setCurrentStep('subjects')}
              className="flex-1 py-2 rounded-lg text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 transition-colors"
            >
              ← 返回修改
            </button>
            <button
              onClick={handleSubmit}
              disabled={!canSubmit}
              className={`flex-[2] py-2.5 rounded-xl text-sm font-medium transition-all ${
                canSubmit
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 shadow-md hover:shadow-lg'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              }`}
            >
              {canSubmit ? '✨ 生成我的志愿方案' : '请完成基本信息和选科'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
