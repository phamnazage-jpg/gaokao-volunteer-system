/**
 * V10 option B · React Router 7 configuration.
 * Replaces Next.js App Router.
 *
 * T-B-26: split heavy vendor pages with React.lazy chunks.
 *   - ShareDialogPage → recharts (chart-vendor 101 KB)
 *   - DataQueryPage → data-query heavy
 *   - ReviewPage + PosterPreviewPage → review/poster
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
import { AdminLoginPage } from './pages/admin/LoginPage';
import { AdminDashboardPage } from './pages/admin/DashboardPage';
import { ForbiddenPage } from './pages/admin/ForbiddenPage';
import { AdminOrdersPage } from './pages/admin/OrdersPage';
import { AdminOrderDetailPage } from './pages/admin/OrderDetailPage';
import { AdminCasesPage } from './pages/admin/CasesPage';
import { AdminCaseDetailPage } from './pages/admin/CaseDetailPage';
import { AdminShareLinkDetailPage } from './pages/admin/ShareLinkDetailPage';
import { AdminShareLinksPage } from './pages/admin/ShareLinksPage';
import { AdminPostersPage } from './pages/admin/PostersPage';
import { AdminScoreLinesPage } from './pages/admin/ScoreLinesPage';
import { AdminRankEstimatorPage } from './pages/admin/RankEstimatorPage';
import { AdminMajorsPage } from './pages/admin/MajorsPage';
import { AdminSchoolsPage } from './pages/admin/SchoolsPage';
import { AdminErrorPage } from './pages/admin/ErrorPage';
import { AppLayout } from './layouts/AppLayout';
import { AdminLayout } from './layouts/AdminLayout';
import { RequireAuth } from './components/admin/RequireAuth';

// T-B-26: lazy chunks downloaded only when users actively visit these pages.
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
  { path: '/admin/login', element: <AdminLoginPage /> },
  { path: '/403', element: <ForbiddenPage /> },
  {
    path: '/admin',
    element: (
      <RequireAuth>
        <AdminLayout />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <AdminDashboardPage /> },
      { path: 'orders', element: <AdminOrdersPage /> },
      { path: 'orders/:orderId', element: <AdminOrderDetailPage /> },
      { path: 'cases', element: <AdminCasesPage /> },
      { path: 'cases/:caseId', element: <AdminCaseDetailPage /> },
      { path: 'share-links', element: <AdminShareLinksPage /> },
      { path: 'share-links/:code', element: <AdminShareLinkDetailPage /> },
      { path: 'posters', element: <AdminPostersPage /> },
      { path: 'score-lines', element: <AdminScoreLinesPage /> },
      { path: 'rank-estimator', element: <AdminRankEstimatorPage /> },
      { path: 'majors', element: <AdminMajorsPage /> },
      { path: 'schools', element: <AdminSchoolsPage /> },
      { path: 'review', element: <ReviewPage /> },
      { path: 'error', element: <AdminErrorPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
];

export const router = typeof window !== 'undefined' ? createBrowserRouter(routes) : createMemoryRouter(routes);

/** Test helper: create an isolated memory router for Vitest rendering. */
export function createTestRouter(initialEntries: string[] = ['/']) {
  return createMemoryRouter(routes, { initialEntries });
}
