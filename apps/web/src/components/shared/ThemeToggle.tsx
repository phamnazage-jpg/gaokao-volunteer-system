/**
 * V10 选项 B · ThemeToggle 组件 (3 主题切换)
 *
 * V10 不变量 D2: 三主题切换 (light/dark/system) + 1.2s 缓动 + SSR/CSR 一致
 *
 * 主题状态存于 useUIStore (Zustand), 实际 class 切换通过 index.html 注入的 inline script 完成
 */
import { useUIStore, type ThemePreference } from '@/stores/ui';

interface ThemeConfig {
  readonly value: ThemePreference;
  readonly label: string;
  readonly icon: string;
}

const THEMES: ReadonlyArray<ThemeConfig> = [
  { value: 'light', label: '亮色', icon: '☀️' },
  { value: 'dark', label: '暗色', icon: '🌙' },
  { value: 'system', label: '系统', icon: '💻' },
];

function applyTheme(pref: ThemePreference): 'light' | 'dark' {
  const resolved = pref === 'system' ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : pref;
  document.documentElement.classList.remove('light', 'dark');
  document.documentElement.classList.add(resolved);
  document.documentElement.style.colorScheme = resolved;
  // 同步给 index.html 内联脚本读取, 避免刷新时主题丢失
  try {
    localStorage.setItem('theme-pref', pref);
  } catch {
    // localStorage 不可用时忽略
  }
  return resolved;
}

export function ThemeToggle() {
  const theme = useUIStore((s) => s.theme);
  const setTheme = useUIStore((s) => s.setTheme);
  const setResolvedTheme = useUIStore((s) => s.setResolvedTheme);

  const handleChange = (next: ThemePreference): void => {
    setTheme(next);
    const resolved = applyTheme(next);
    setResolvedTheme(resolved);
  };

  return (
    <div className="theme-toggle inline-flex" role="radiogroup" aria-label="主题切换">
      {THEMES.map((t) => (
        <button
          key={t.value}
          type="button"
          className={`theme-toggle-btn px-2 py-1 text-xs rounded ${
            theme === t.value ? 'bg-blue-100 text-blue-700' : 'text-gray-500 hover:bg-gray-100'
          }`}
          onClick={() => handleChange(t.value)}
          role="radio"
          aria-checked={theme === t.value}
          aria-label={t.label}
          title={t.label}
        >
          {t.icon}
        </button>
      ))}
    </div>
  );
}