/**
 * V10 Sprint 4 · T-B-26 · route hover prefetch
 *
 * When the user hovers a navigation item, preload the matching lazy chunk.
 * The browser caches it while the network is idle, so the next click can load from cache.
 *
 * Only prefetch routes the user is likely to visit; hover is the intent signal.
 * Do not prefetch every route proactively because that wastes bandwidth.
 */
import { useCallback } from 'react';

// Keep these aligned with router.tsx lazy imports, reusing the same dynamic import paths.
const LAZY_ROUTE_LOADERS: Record<string, () => Promise<unknown>> = {
  '/share': () => import('@/pages/ShareDialogPage'),
  '/data-query': () => import('@/pages/DataQueryPage'),
  '/review': () => import('@/pages/ReviewPage'),
  '/poster': () => import('@/pages/PosterPreviewPage'),
};

/**
 * Return a prefetch function that accepts a path and triggers the matching chunk download.
 */
export function usePrefetchLazyRoute() {
  return useCallback((path: string) => {
    const loader = LAZY_ROUTE_LOADERS[path];
    if (loader) {
      // Call the loader without reading the result; Vite/Rollup registers the dynamic import for modulepreload.
      void loader().catch(() => {
        // Ignore failures; prefetch should never affect the user flow.
      });
    }
  }, []);
}

/**
 * Return the loader map for router.tsx reuse, ensuring prefetch and routing share import paths.
 */
export const lazyRouteLoaders = LAZY_ROUTE_LOADERS;
