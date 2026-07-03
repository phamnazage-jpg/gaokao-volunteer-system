'use client';

/**
 * ProgressSteps — 进度感知组件
 * 用于信息收集阶段的进度提示
 */

import React from 'react';

interface Step {
  key: string;
  label: string;
  done: boolean;
}

interface Props {
  steps: Step[];
  currentStep?: string;
  className?: string;
}

export function ProgressSteps({ steps, currentStep, className = '' }: Props) {
  const activeIndex = steps.findIndex((s) => s.key === currentStep);
  const totalDone = steps.filter((s) => s.done).length;

  return (
    <div className={`inline-flex items-center gap-1.5 text-xs ${className}`} role="progressbar" aria-label={`已完成 ${totalDone}/${steps.length} 步`} aria-valuenow={totalDone} aria-valuemin={0} aria-valuemax={steps.length}>
      {steps.map((step, idx) => {
        const isDone = step.done;
        const isActive = step.key === currentStep;

        return (
          <React.Fragment key={step.key}>
            <span
              className={`w-2 h-2 rounded-full transition-colors ${
                isDone
                  ? 'bg-green-500'
                  : isActive
                    ? 'bg-brand-500 ring-2 ring-brand-200'
                    : 'bg-gray-200'
              }`}
              style={isActive ? { backgroundColor: 'var(--brand-500)', boxShadow: '0 0 0 2px rgba(59, 130, 246, 0.2)' } : isDone ? { backgroundColor: 'var(--color-safe)' } : {}}
            />
            <span
              className={`${
                isActive ? 'text-brand-600 font-medium' : isDone ? 'text-green-600' : 'text-gray-400'
              }`}
              style={isActive ? { color: 'var(--brand-600)' } : isDone ? { color: 'var(--color-safe)' } : {}}
            >
              {step.label}
            </span>
            {idx < steps.length - 1 && (
              <span className="w-3 h-px bg-gray-200" />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

/**
 * 信息收集进度 — 预置步骤
 */
export function InfoCollectionProgress({
  province,
  score,
  subjects,
}: {
  province?: string;
  score?: number;
  subjects?: string[];
}) {
  const steps = [
    { key: 'province', label: '省份', done: !!province },
    { key: 'score', label: '分数', done: !!score },
    { key: 'subjects', label: '选科', done: !!subjects?.length },
  ];

  const currentKey = !province ? 'province' : !score ? 'score' : !subjects?.length ? 'subjects' : undefined;

  return (
    <ProgressSteps
      steps={steps}
      currentStep={currentKey}
      className="bg-white/90 border border-gray-100 rounded-full px-3 py-1.5 shadow-sm"
    />
  );
}
