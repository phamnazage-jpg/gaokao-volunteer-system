'use client';

/**
 * 主题切换组件
 * 用法: <ThemeToggle /> — 放在 Header 或 Sidebar 中
 */

import React, { useState, useEffect } from 'react';
import { getEffectiveTheme, setTheme, type Theme } from '@/lib/theme';

const THEMES: { value: Theme; label: string; icon: string }[] = [
  { value: 'light', label: '亮色', icon: '☀️' },
  { value: 'dark', label: '暗色', icon: '🌙' },
  { value: 'system', label: '系统', icon: '💻' },
];

export function ThemeToggle() {
  const [current, setCurrent] = useState<Theme>('system');

  useEffect(() => {
    setCurrent(getEffectiveTheme());
  }, []);

  const handleChange = (theme: Theme) => {
    setTheme(theme);
    setCurrent(theme);
  };

  return (
    <div
      className="theme-toggle"
      role="radiogroup"
      aria-label="主题切换"
    >
      {THEMES.map((t) => (
        <button
          key={t.value}
          className={`theme-toggle-btn ${current === t.value ? 'active' : ''}`}
          onClick={() => handleChange(t.value)}
          role="radio"
          aria-checked={current === t.value}
          aria-label={t.label}
          title={t.label}
        >
          {t.icon}
        </button>
      ))}
    </div>
  );
}
