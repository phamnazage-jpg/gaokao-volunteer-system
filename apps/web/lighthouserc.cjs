/**
 * V10 · Sprint 4 · T-B-24 · Lighthouse CI 配置
 *
 * G3 闸门真实化：P/A/B/S 均 ≥ 90
 * - perf: 性能（首屏加载、TTI、TBT）
 * - a11y: 无障碍（WCAG 2.1 AA）
 * - best-practices: HTTPS / CSP / console errors
 * - seo: meta tags / viewport
 *
 * 注意：mobile 测试（默认 form factor = mobile）更严格
 */
module.exports = {
  ci: {
    collect: {
      // LHCI 由 treosh/lighthouse-ci-action 自动启动 vite preview @ 8080
      url: [
        'http://127.0.0.1:8080/',
        'http://127.0.0.1:8080/data-query',
        'http://127.0.0.1:8080/plans',
        'http://127.0.0.1:8080/about',
      ],
      numberOfRuns: 3, // 取 P75（median）
      settings: {
        // P75 算分（默认 median = P50）
        preset: 'desktop',
        chromeFlags: '--no-sandbox --headless=new',
      },
    },
    assert: {
      // G3 闸门：每类 ≥ 90
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['error', { minScore: 0.9 }],
        'categories:seo': ['error', { minScore: 0.9 }],
      },
    },
    upload: {
      target: 'temporary-public-storage', // 公开 storage 30 天；后续接 LHCI server
    },
  },
};