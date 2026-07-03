/**
 * V10 选项 B · React Router 7 配置
 * 替代 Next.js App Router
 */
import { createBrowserRouter, createMemoryRouter, type RouteObject } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { PlansPage } from './pages/PlansPage';
import { PlanComparePage } from './pages/PlanComparePage';
import { PlanDetailPage } from './pages/PlanDetailPage';
import { ConsultationsPage } from './pages/ConsultationsPage';
import { AboutPage } from './pages/AboutPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { AppLayout } from './layouts/AppLayout';

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