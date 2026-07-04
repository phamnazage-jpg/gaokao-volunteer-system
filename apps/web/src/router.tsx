/**
 * V10 选项 B · React Router 7 配置
 * 替代 Next.js App Router
 *
 * T-B-26: 重 vendor 的 page 用 React.lazy 拆 chunk
 *   - ShareDialogPage → recharts (chart-vendor 101 KB)
 *   - DataQueryPage → 数据查询密集
 *   - ReviewPage + PosterPreviewPage → 审核/海报
 */
import { lazy } from 'react';
import { createBrowserRouter, createMemoryRouter, type RouteObject } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { PlansPage } from './pages/PlansPage';
import { PlanComparePage } from './pages/PlanComparePage';
import { PlanDetailPage } from './pages/PlanDetailPage';
import { ConsultationsPage } from './pages/ConsultationsPage';
import { AboutPage } from './pages/AboutPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { PortalPage } from './pages/PortalPage';
import { AppLayout } from './layouts/AppLayout';

// T-B-26: lazy chunks — 这些 page 在用户主动访问时才下载
const ShareDialogPage = lazy(() => import('./pages/ShareDialogPage').then((m) => ({ default: m.ShareDialogPage })));
const DataQueryPage = lazy(() => import('./pages/DataQueryPage').then((m) => ({ default: m.DataQueryPage })));
const ReviewPage = lazy(() => import('./pages/ReviewPage').then((m) => ({ default: m.ReviewPage })));
const PosterPreviewPage = lazy(() => import('./pages/PosterPreviewPage').then((m) => ({ default: m.PosterPreviewPage })));

const routes: RouteObject[] = [
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'plans', element: <PlansPage /> },
      { path: 'plans/compare', element: <PlanComparePage /> },
      { path: 'plans/:planId', element: <PlanDetailPage /> },
      { path: 'consultations', element: <ConsultationsPage /> },
      { path: 'share', element: <ShareDialogPage /> },
      { path: 'data-query', element: <DataQueryPage /> },
      { path: 'review', element: <ReviewPage /> },
      { path: 'poster', element: <PosterPreviewPage /> },
      { path: 'portal/:token', element: <PortalPage /> },
      { path: 'about', element: <AboutPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
];

export const router = typeof window !== 'undefined' ? createBrowserRouter(routes) : createMemoryRouter(routes);

/** 测试工具: 创建独立的 memory router (Vitest 渲染用) */
export function createTestRouter(initialEntries: string[] = ['/']) {
  return createMemoryRouter(routes, { initialEntries });
}