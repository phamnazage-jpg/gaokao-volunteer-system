import { useIntl } from 'react-intl';
import { useUIStore, type ThemePreference } from '@/stores/ui';

interface ThemeConfig {
  readonly value: ThemePreference;
  readonly labelKey: string;
  readonly icon: string;
}

const THEMES: ReadonlyArray<ThemeConfig> = [
  { value: 'light', labelKey: 'themeToggle.light', icon: '☀️' },
  { value: 'dark', labelKey: 'themeToggle.dark', icon: '🌙' },
  { value: 'system', labelKey: 'themeToggle.system', icon: '💻' },
];

function applyTheme(pref: ThemePreference): 'light' | 'dark' {
  const resolved = pref === 'system' ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : pref;
  document.documentElement.classList.remove('light', 'dark');
  document.documentElement.classList.add(resolved);
  document.documentElement.style.colorScheme = resolved;
  try {
    localStorage.setItem('theme-pref', pref);
  } catch {
    // Ignore storage failures in restricted browser contexts.
  }
  return resolved;
}

export function ThemeToggle() {
  const intl = useIntl();
  const theme = useUIStore((s) => s.theme);
  const setTheme = useUIStore((s) => s.setTheme);
  const setResolvedTheme = useUIStore((s) => s.setResolvedTheme);

  const handleChange = (next: ThemePreference): void => {
    setTheme(next);
    const resolved = applyTheme(next);
    setResolvedTheme(resolved);
  };

  return (
    <div className="theme-toggle inline-flex" role="radiogroup" aria-label={intl.formatMessage({ id: 'themeToggle.ariaLabel' })}>
      {THEMES.map((t) => (
        <button
          key={t.value}
          type="button"
          className={`theme-toggle-btn px-2 py-1 text-xs rounded ${
            theme === t.value ? 'bg-blue-100 text-blue-700 dark:bg-blue-950/60 dark:text-blue-200' : 'text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100'
          }`}
          onClick={() => handleChange(t.value)}
          role="radio"
          aria-checked={theme === t.value}
          aria-label={intl.formatMessage({ id: t.labelKey })}
          title={intl.formatMessage({ id: t.labelKey })}
        >
          {t.icon}
        </button>
      ))}
    </div>
  );
}
