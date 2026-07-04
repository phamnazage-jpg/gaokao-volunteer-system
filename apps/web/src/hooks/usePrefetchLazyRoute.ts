/**
 * V10 Sprint 4 · T-B-26 · 路由 hover prefetch
 *
 * 用户 hover navigation item 时，触发对应 lazy chunk 的预下载。
 * 网络空闲时浏览器会缓存，下一次点击即从缓存加载。
 *
 * 注意：仅 prefetch 用户**可能**访问的路由（hover 才是意图信号）；
 * 不主动 prefetch 所有路由（浪费带宽）。
 */
import { useCallback } from 'react';

// 与 router.tsx 中 lazy import 对齐 — 复用同一个 dynamic import() 路径
const LAZY_ROUTE_LOADERS: Record<string, () => Promise<unknown>> = {
  '/share': () => import('@/pages/ShareDialogPage'),
  '/data-query': () => import('@/pages/DataQueryPage'),
  '/review': () => import('@/pages/ReviewPage'),
  '/poster': () => import('@/pages/PosterPreviewPage'),
};

/**
 * 返回一个 prefetch 函数，传 path 调用即可触发对应 chunk 下载
 */
export function usePrefetchLazyRoute() {
  return useCallback((path: string) => {
    const loader = LAZY_ROUTE_LOADERS[path];
    if (loader) {
      // 调用 loader 但不取结果 — Vite/Rollup 会把动态 import 注册到 modulepreload
      void loader().catch(() => {
        // 静默失败：prefetch 失败不应影响用户
      });
    }
  }, []);
}

/**
 * 直接返回 loader map（供 router.tsx 复用，确保 prefetch 与 route 用同一个 import 路径）
 */
export const lazyRouteLoaders = LAZY_ROUTE_LOADERS;