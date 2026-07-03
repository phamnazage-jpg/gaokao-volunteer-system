/**
 * 主题管理系统
 * 支持三种模式：light（亮色）、dark（暗色）、system（跟随系统）
 *
 * 使用方式：
 * - 在 layout.tsx 的 <head> 中调用 initTheme()（阻塞渲染前的闪白）
 * - 在组件中使用 setTheme() 切换主题
 * - 在 CSS 中通过 var(--xxx) 使用设计 Token
 */

export type Theme = "light" | "dark" | "system";

const THEME_KEY = "theme";

/**
 * 页面加载时第一时间调用（在 <head> 中，阻塞渲染）
 * 防止暗色模式用户看到闪白
 */
export function initThemeScript(): string {
  // 返回一段内联 JS 字符串，放在 <head> 的 <script> 中
  return `
    (function() {
      var stored = localStorage.getItem('${THEME_KEY}');
      if (stored === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
      } else if (stored === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
      }
      // system: 不做任何事，由 CSS @media 处理
    })();
  `;
}

/**
 * 获取当前生效的主题
 */
export function getEffectiveTheme(): Theme {
  if (typeof window === "undefined") return "system";
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return "system";
}

/**
 * 设置主题
 */
export function setTheme(theme: Theme): void {
  if (typeof window === "undefined") return;

  if (theme === "system") {
    document.documentElement.removeAttribute("data-theme");
    localStorage.removeItem(THEME_KEY);
  } else {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
  }
}

/**
 * 判断当前是否处于暗色模式（用于 React 组件）
 */
export function isDarkMode(): boolean {
  if (typeof window === "undefined") return false;
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === "dark") return true;
  if (stored === "light") return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}
