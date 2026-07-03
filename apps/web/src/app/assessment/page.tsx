'use client';

import React, { useState } from 'react';
import Link from 'next/link';

interface Question {
  id: number;
  title: string;
  options: {
    label: string;
    text: string;
    type: 'R' | 'I' | 'S' | 'A';
  }[];
}

const questions: Question[] = [
  {
    id: 1,
    title: '你更喜欢哪种工作方式？',
    options: [
      { label: 'A', text: '动手操作，解决实际问题', type: 'R' },
      { label: 'B', text: '思考分析，研究抽象概念', type: 'I' },
      { label: 'C', text: '与人沟通，协调组织事务', type: 'S' },
      { label: 'D', text: '创意表达，产出独特作品', type: 'A' },
    ],
  },
  {
    id: 2,
    title: '哪种活动最让你感到充实？',
    options: [
      { label: 'A', text: '拆解和修理物品', type: 'R' },
      { label: 'B', text: '阅读科学文章或解数学题', type: 'I' },
      { label: 'C', text: '组织朋友聚会或团队活动', type: 'S' },
      { label: 'D', text: '绘画、写作或音乐创作', type: 'A' },
    ],
  },
  {
    id: 3,
    title: '面对问题时，你通常？',
    options: [
      { label: 'A', text: '立即动手尝试解决', type: 'R' },
      { label: 'B', text: '先分析问题的根源', type: 'I' },
      { label: 'C', text: '找朋友或同事讨论', type: 'S' },
      { label: 'D', text: '用创新的方式重新定义问题', type: 'A' },
    ],
  },
  {
    id: 4,
    title: '你更擅长？',
    options: [
      { label: 'A', text: '使用工具和设备', type: 'R' },
      { label: 'B', text: '逻辑推理和数据分析', type: 'I' },
      { label: 'C', text: '说服和激励他人', type: 'S' },
      { label: 'D', text: '想象和创造新事物', type: 'A' },
    ],
  },
  {
    id: 5,
    title: '在团队中，你更倾向于？',
    options: [
      { label: 'A', text: '负责具体的执行任务', type: 'R' },
      { label: 'B', text: '提供分析和策略建议', type: 'I' },
      { label: 'C', text: '协调成员关系和沟通', type: 'S' },
      { label: 'D', text: '提出新颖的想法和方向', type: 'A' },
    ],
  },
  {
    id: 6,
    title: '哪种学习方式最适合你？',
    options: [
      { label: 'A', text: '动手实践、做实验', type: 'R' },
      { label: 'B', text: '阅读教材、听讲座', type: 'I' },
      { label: 'C', text: '小组讨论、互相教学', type: 'S' },
      { label: 'D', text: '独立探索、自由创作', type: 'A' },
    ],
  },
  {
    id: 7,
    title: '你对哪种信息更敏感？',
    options: [
      { label: 'A', text: '物理空间和机械原理', type: 'R' },
      { label: 'B', text: '数字、图表和公式', type: 'I' },
      { label: 'C', text: '人的情绪和社交信号', type: 'S' },
      { label: 'D', text: '色彩、形状和美学', type: 'A' },
    ],
  },
  {
    id: 8,
    title: '哪种工作环境你最舒适？',
    options: [
      { label: 'A', text: '实验室或工作坊', type: 'R' },
      { label: 'B', text: '安静的办公室或图书馆', type: 'I' },
      { label: 'C', text: '开放式的协作空间', type: 'S' },
      { label: 'D', text: '灵活自由的创意空间', type: 'A' },
    ],
  },
  {
    id: 9,
    title: '你更看重工作的？',
    options: [
      { label: 'A', text: '稳定性和实用性', type: 'R' },
      { label: 'B', text: '专业性和深度', type: 'I' },
      { label: 'C', text: '人际关系和影响力', type: 'S' },
      { label: 'D', text: '自由度和创造性', type: 'A' },
    ],
  },
  {
    id: 10,
    title: '未来5年，你希望成为？',
    options: [
      { label: 'A', text: '技术专家/工程师', type: 'R' },
      { label: 'B', text: '科学家/研究员', type: 'I' },
      { label: 'C', text: '管理者/领导者', type: 'S' },
      { label: 'D', text: '艺术家/创业者', type: 'A' },
    ],
  },
];

const typeInfo: Record<string, { name: string; desc: string; majors: string; color: string }> = {
  R: { name: '动手型 (R)', desc: '喜欢实际操作，擅长使用工具和设备解决具体问题', majors: '工学类（计算机、机械、电子等）', color: 'bg-orange-500' },
  I: { name: '思考型 (I)', desc: '喜欢研究和分析，擅长逻辑推理和抽象思维', majors: '理学类（数学、物理、化学等）', color: 'bg-blue-500' },
  S: { name: '社交型 (S)', desc: '喜欢与人交往，擅长沟通协调和组织管理', majors: '经管/教育/法学类', color: 'bg-green-500' },
  A: { name: '创造型 (A)', desc: '喜欢创意表达，擅长想象和创造独特作品', majors: '文学/艺术/设计类', color: 'bg-purple-500' },
};

export default function AssessmentPage() {
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState<(string | null)[]>(Array(10).fill(null));
  const [showResult, setShowResult] = useState(false);

  const handleSelect = (type: string) => {
    const newAnswers = [...answers];
    newAnswers[current] = type;
    setAnswers(newAnswers);
  };

  const handleNext = () => {
    if (current < 9) {
      setCurrent(current + 1);
    } else {
      setShowResult(true);
    }
  };

  const handlePrev = () => {
    if (current > 0) {
      setCurrent(current - 1);
    }
  };

  const calculateResult = () => {
    const scores: Record<string, number> = { R: 0, I: 0, S: 0, A: 0 };
    answers.forEach((answer) => {
      if (answer && scores[answer] !== undefined) {
        scores[answer]++;
      }
    });
    return scores;
  };

  const question = questions[current];

  // Result view
  if (showResult) {
    const scores = calculateResult();
    const maxType = Object.entries(scores).reduce((a, b) => (b[1] > a[1] ? b : a))[0];
    const info = typeInfo[maxType];
    const total = Object.values(scores).reduce((a, b) => a + b, 0);

    return (
      <div className="flex flex-col min-h-screen bg-gray-50">
        <header className="flex items-center px-4 py-3 bg-white border-b border-gray-100">
          <Link href="/" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span>返回对话</span>
          </Link>
          <h1 className="flex-1 text-center text-sm font-bold text-gray-800 -ml-8">测评结果</h1>
        </header>

        <div className="flex-1 flex items-start justify-center px-4 py-8">
          <div className="w-full max-w-xl space-y-6">
            {/* Result card */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-12 h-12 ${info.color} rounded-full flex items-center justify-center text-white text-lg font-bold`}>
                  {maxType}
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-800">{info.name}</h2>
                  <p className="text-sm text-gray-500">{info.desc}</p>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 mb-6">
                <p className="text-sm text-blue-800 font-medium mb-1">推荐专业方向</p>
                <p className="text-lg font-bold text-blue-900">{info.majors}</p>
              </div>

              {/* Dimension scores */}
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">各维度得分</h3>
                {(['R', 'I', 'S', 'A'] as const).map((type) => {
                  const t = typeInfo[type];
                  const pct = total > 0 ? (scores[type] / total) * 100 : 0;
                  return (
                    <div key={type} className="flex items-center gap-3">
                      <span className="text-xs font-medium text-gray-600 w-24 shrink-0">{t.name}</span>
                      <div className="flex-1 h-2.5 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${t.color} rounded-full transition-all duration-700 ease-out`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium text-gray-500 w-6 text-right">{scores[type]}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex gap-3">
              <Link
                href="/"
                className="flex-1 py-3 bg-white border border-gray-200 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors text-center"
              >
                返回对话
              </Link>
              <button
                onClick={() => {
                  try {
                    const existing = localStorage.getItem('userPreferences') || '{}';
                    const prefs = JSON.parse(existing);
                    prefs.assessmentType = maxType;
                    prefs.assessmentScores = scores;
                    localStorage.setItem('userPreferences', JSON.stringify(prefs));
                  } catch {}
                }}
                className="flex-1 py-3 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 transition-colors"
              >
                加入偏好设置
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      {/* Header */}
      <header className="flex items-center px-4 py-3 bg-white border-b border-gray-100">
        <Link href="/" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>返回对话</span>
        </Link>
        <h1 className="flex-1 text-center text-sm font-bold text-gray-800 -ml-8">兴趣倾向测评</h1>
      </header>

      <div className="flex-1 flex items-start justify-center px-4 py-8">
        <div className="w-full max-w-xl space-y-6">
          {/* Progress bar */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex gap-1">
                {questions.map((q, i) => (
                  <div
                    key={q.id}
                    className={`w-2.5 h-2.5 rounded-full transition-colors ${
                      answers[i] ? 'bg-blue-500' : 'bg-gray-200'
                    }`}
                  />
                ))}
              </div>
              <span className="text-xs font-medium text-gray-500">
                {current + 1}/{questions.length}
              </span>
            </div>
            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${((current + 1) / questions.length) * 100}%` }}
              />
            </div>
          </div>

          {/* Question card */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <p className="text-xs font-medium text-blue-600 mb-2">
              第 {question.id} 题
            </p>
            <h2 className="text-xl font-bold text-gray-800 mb-6">{question.title}</h2>

            <div className="space-y-3">
              {question.options.map((option) => {
                const isSelected = answers[current] === option.type;
                return (
                  <button
                    key={option.label}
                    onClick={() => handleSelect(option.type)}
                    className={`w-full text-left px-4 py-3.5 rounded-xl border-2 transition-all ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50 shadow-sm'
                        : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/50'
                    }`}
                  >
                    <span className="text-sm text-gray-700">{option.text}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Navigation buttons */}
          <div className="flex gap-3">
            <button
              onClick={handlePrev}
              disabled={current === 0}
              className={`flex-1 py-3 rounded-xl text-sm font-medium transition-colors ${
                current === 0
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              上一题
            </button>
            <button
              onClick={handleNext}
              disabled={!answers[current]}
              className={`flex-1 py-3 rounded-xl text-sm font-medium transition-colors ${
                !answers[current]
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : current === 9
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {current === 9 ? '查看结果' : '下一题'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
