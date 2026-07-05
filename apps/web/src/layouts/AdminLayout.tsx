import { Suspense } from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { FormattedMessage, useIntl } from 'react-intl';
import { BarChart3, Database, FileText, Home, Link2, LogOut, School, ShieldCheck, TrendingUp, Users } from 'lucide-react';
import { LocaleSwitcher } from '@/components/shared/LocaleSwitcher';
import { RouteFallback } from '@/components/shared/RouteFallback';
import { ThemeToggle } from '@/components/shared/ThemeToggle';
import { AdminErrorPage } from '@/pages/admin/ErrorPage';
import { useUserStore } from '@/stores/user';

const adminNavItems = [
  { to: '/admin', labelKey: 'admin.nav.dashboard', icon: Home },
  { to: '/admin/orders', labelKey: 'admin.nav.orders', icon: FileText },
  { to: '/admin/cases', labelKey: 'admin.nav.cases', icon: Users },
  { to: '/admin/share-links', labelKey: 'admin.nav.shareLinks', icon: Link2 },
  { to: '/admin/score-lines', labelKey: 'admin.nav.scoreLines', icon: Database },
  { to: '/admin/rank-estimator', labelKey: 'admin.nav.rankEstimator', icon: TrendingUp },
  { to: '/admin/majors', labelKey: 'admin.nav.majors', icon: BarChart3 },
  { to: '/admin/schools', labelKey: 'admin.nav.schools', icon: School },
  { to: '/admin/review', labelKey: 'admin.nav.review', icon: ShieldCheck },
  { to: '/admin/posters', labelKey: 'admin.nav.posters', icon: BarChart3 },
] as const;

export function AdminLayout() {
  const intl = useIntl();
  const location = useLocation();
  const navigate = useNavigate();
  const userName = useUserStore((state) => state.name);
  const logout = useUserStore((state) => state.logout);

  const handleLogout = (): void => {
    logout();
    void navigate('/admin/login', { replace: true });
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-100">
      <aside className="fixed inset-y-0 left-0 hidden w-72 border-r border-slate-200 bg-white/95 p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900/95 lg:flex lg:flex-col">
        <Link to="/admin" className="flex items-center gap-3 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500">
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-blue-600 text-lg font-bold text-white">G</span>
          <span>
            <span className="block text-sm font-bold">
              <FormattedMessage id="app.name" />
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              <FormattedMessage id="app.adminPortal" />
            </span>
          </span>
        </Link>

        <nav className="mt-8 flex flex-col gap-1" aria-label={intl.formatMessage({ id: 'admin.nav.ariaLabel' })}>
          {adminNavItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/admin'}
                className={({ isActive }) =>
                  `flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm font-medium transition ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 dark:bg-blue-500/15 dark:text-blue-200'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'
                  }`
                }
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                {intl.formatMessage({ id: item.labelKey })}
              </NavLink>
            );
          })}
        </nav>

        <div className="mt-auto rounded-2xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-500 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-400">
          <p className="font-medium text-slate-700 dark:text-slate-200">
            <FormattedMessage id="admin.currentUser" />
          </p>
          <p className="mt-1 truncate">{userName ?? intl.formatMessage({ id: 'admin.unnamedUser' })}</p>
        </div>
      </aside>

      <div className="lg:pl-72">
        <header className="sticky top-0 z-20 flex min-h-16 items-center justify-between border-b border-slate-200 bg-white/90 px-4 backdrop-blur dark:border-slate-800 dark:bg-slate-900/90 sm:px-6">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-blue-600 dark:text-blue-300">
              <FormattedMessage id="admin.header.sprint" />
            </p>
            <h1 className="text-base font-semibold text-slate-950 dark:text-white">
              <FormattedMessage id="admin.header.title" />
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <LocaleSwitcher />
            <ThemeToggle />
            <button
              type="button"
              onClick={handleLogout}
              className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-slate-200 px-3 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
              <FormattedMessage id="admin.logout" />
            </button>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
          <ErrorBoundary fallbackRender={({ resetErrorBoundary }) => <AdminErrorPage onRetry={resetErrorBoundary} />} resetKeys={[location.pathname]}>
            <Suspense fallback={<RouteFallback />}>
              <Outlet />
            </Suspense>
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
