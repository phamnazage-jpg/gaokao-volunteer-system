import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { FormattedMessage, useIntl } from 'react-intl';
import { LockKeyhole, ShieldCheck, UserRound } from 'lucide-react';
import { z } from 'zod';
import { SubmitButton } from '@/components/shared/SubmitButton';
import { toast } from '@/components/shared/Toast';
import { apiClient } from '@/lib/api-client';
import { getLocalizedApiErrorMessage } from '@/lib/error-messages';
import { useUserStore } from '@/stores/user';

function createLoginSchema(formatMessage: ReturnType<typeof useIntl>['formatMessage']) {
  return z.object({
    username: z.string().trim().min(1, formatMessage({ id: 'admin.login.validation.username' })).max(64),
    password: z.string().min(1, formatMessage({ id: 'admin.login.validation.password' })).max(256),
    remember: z.boolean().default(true),
  });
}

const loginResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string().default('bearer'),
  expires_in: z.number().int().positive(),
});

type LoginFormValues = z.infer<ReturnType<typeof createLoginSchema>>;

interface LocationState {
  from?: string;
}

export function AdminLoginPage() {
  const intl = useIntl();
  const navigate = useNavigate();
  const location = useLocation();
  const isLoggedIn = useUserStore((state) => state.isLoggedIn);
  const setAdminSession = useUserStore((state) => state.setAdminSession);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const from = (location.state as LocationState | null)?.from ?? '/admin';
  const loginSchema = createLoginSchema(intl.formatMessage);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
      remember: true,
    },
  });

  if (isLoggedIn) {
    return <Navigate to="/admin" replace />;
  }

  const onSubmit = async (values: LoginFormValues): Promise<void> => {
    setSubmitError(null);
    try {
      const login = await apiClient.post('/auth/login', { username: values.username, password: values.password }, loginResponseSchema);
      setAdminSession({
        username: values.username,
        accessToken: login.access_token,
        tokenType: login.token_type,
        expiresIn: login.expires_in,
      });
      toast.success(intl.formatMessage({ id: 'admin.login.toastSuccess' }), {
        description: intl.formatMessage({ id: 'admin.login.toastSuccessDescription' }),
      });
      void navigate(from, { replace: true });
    } catch (error) {
      const errorLike = error as { code?: unknown; message?: unknown };
      const code = typeof errorLike.code === 'string' ? errorLike.code : undefined;
      const fallback = typeof errorLike.message === 'string' ? errorLike.message : undefined;
      setSubmitError(getLocalizedApiErrorMessage(code)?.message ?? fallback ?? intl.formatMessage({ id: 'admin.login.genericError' }));
    }
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,#dbeafe,transparent_32rem),linear-gradient(135deg,#f8fafc,#eff6ff_50%,#f8fafc)] px-4 py-10 text-slate-950 dark:bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.24),transparent_30rem),linear-gradient(135deg,#020617,#0f172a_55%,#111827)] dark:text-slate-100">
      <div className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-6xl items-center gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="hidden lg:block">
          <p className="inline-flex rounded-full border border-blue-200 bg-white/70 px-3 py-1 text-xs font-semibold text-blue-700 shadow-sm dark:border-blue-500/30 dark:bg-blue-500/10 dark:text-blue-200">
            Sprint 7 · Admin Portal
          </p>
          <h1 className="mt-6 max-w-xl text-5xl font-black leading-tight tracking-tight text-slate-950 dark:text-white">
            <FormattedMessage id="admin.login.heroTitle" />
          </h1>
          <p className="mt-5 max-w-lg text-base leading-7 text-slate-600 dark:text-slate-300">
            <FormattedMessage id="admin.login.heroDescription" />
          </p>
          <div className="mt-8 grid max-w-lg grid-cols-2 gap-3">
            {['admin.login.featureAuth', 'admin.login.featureGuard', 'admin.login.featurePersistence', 'admin.login.featureDarkMode'].map((messageId) => (
              <div key={messageId} className="rounded-2xl border border-white/70 bg-white/75 p-4 text-sm font-medium shadow-sm dark:border-slate-700 dark:bg-slate-900/75">
                <FormattedMessage id={messageId} />
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-[2rem] border border-white/80 bg-white/90 p-6 shadow-2xl shadow-blue-900/10 backdrop-blur dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-black/30 sm:p-8">
          <div className="flex items-center gap-3">
            <span className="grid h-12 w-12 place-items-center rounded-2xl bg-blue-600 text-white">
              <ShieldCheck className="h-6 w-6" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-2xl font-bold text-slate-950 dark:text-white">
                <FormattedMessage id="admin.login.title" />
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                <FormattedMessage id="admin.login.realHint" />
              </p>
            </div>
          </div>

          <form className="mt-8 space-y-5" onSubmit={(event) => void handleSubmit(onSubmit)(event)}>
            <div>
              <label htmlFor="admin-username" className="text-sm font-medium text-slate-700 dark:text-slate-200">
                <FormattedMessage id="admin.login.usernameLabel" />
              </label>
              <div className="relative mt-2">
                <UserRound className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                <input
                  id="admin-username"
                  type="text"
                  autoComplete="username"
                  placeholder="admin"
                  className="min-h-12 w-full rounded-2xl border border-slate-200 bg-white px-11 text-sm text-slate-950 shadow-sm transition placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                  aria-invalid={Boolean(errors.username)}
                  {...register('username')}
                />
              </div>
              {errors.username && <p className="mt-2 text-xs text-red-600 dark:text-red-300">{errors.username.message}</p>}
            </div>

            <div>
              <label htmlFor="admin-password" className="text-sm font-medium text-slate-700 dark:text-slate-200">
                <FormattedMessage id="admin.login.passwordLabel" />
              </label>
              <div className="relative mt-2">
                <LockKeyhole className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                <input
                  id="admin-password"
                  type="password"
                  autoComplete="current-password"
                  className="min-h-12 w-full rounded-2xl border border-slate-200 bg-white px-11 text-sm text-slate-950 shadow-sm transition placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                  aria-invalid={Boolean(errors.password)}
                  {...register('password')}
                />
              </div>
              {errors.password && <p className="mt-2 text-xs text-red-600 dark:text-red-300">{errors.password.message}</p>}
            </div>

            <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
              <input type="checkbox" className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500" {...register('remember')} />
              <FormattedMessage id="admin.login.rememberLabel" />
            </label>

            {submitError && (
              <p role="alert" className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
                {submitError}
              </p>
            )}

            <SubmitButton
              isSubmitting={isSubmitting}
              idleLabel={intl.formatMessage({ id: 'admin.login.submit' })}
              submittingLabel={intl.formatMessage({ id: 'admin.login.submitting' })}
              className="w-full bg-blue-600 text-white hover:bg-blue-700"
            />
          </form>
        </section>
      </div>
    </main>
  );
}
