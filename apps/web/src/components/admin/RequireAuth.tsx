import { useEffect, useState, type ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { z } from 'zod';
import { RouteFallback } from '@/components/shared/RouteFallback';
import { apiClient } from '@/lib/api-client';
import { useUserStore } from '@/stores/user';

interface RequireAuthProps {
  children: ReactNode;
  requireAdmin?: boolean;
}

const currentUserSchema = z.object({
  id: z.number(),
  username: z.string(),
  role: z.string(),
  is_active: z.boolean(),
  created_at: z.string(),
  last_login_at: z.string().nullable().optional(),
});

type AuthCheckState = 'checking' | 'authenticated' | 'anonymous' | 'forbidden';

function hasActiveToken(token: string | null, tokenExpiresAt: number | null): boolean {
  return Boolean(token && tokenExpiresAt && tokenExpiresAt > Date.now());
}

export function RequireAuth({ children, requireAdmin = true }: RequireAuthProps) {
  const location = useLocation();
  const token = useUserStore((state) => state.token);
  const tokenExpiresAt = useUserStore((state) => state.tokenExpiresAt);
  const logout = useUserStore((state) => state.logout);
  const [authState, setAuthState] = useState<AuthCheckState>(() => (hasActiveToken(token, tokenExpiresAt) ? 'checking' : 'anonymous'));

  useEffect(() => {
    let cancelled = false;

    if (!hasActiveToken(token, tokenExpiresAt)) {
      logout();
      setAuthState('anonymous');
      return () => {
        cancelled = true;
      };
    }

    setAuthState('checking');
    void apiClient
      .get('/auth/me', currentUserSchema)
      .then((user) => {
        if (cancelled) {
          return;
        }
        if (!user.is_active) {
          logout();
          setAuthState('anonymous');
          return;
        }
        if (requireAdmin && user.role !== 'admin') {
          setAuthState('forbidden');
          return;
        }
        setAuthState('authenticated');
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        logout();
        setAuthState('anonymous');
      });

    return () => {
      cancelled = true;
    };
  }, [logout, requireAdmin, token, tokenExpiresAt]);

  if (authState === 'anonymous') {
    return <Navigate to="/admin/login" replace state={{ from: location.pathname }} />;
  }

  if (authState === 'forbidden') {
    return <Navigate to="/403" replace />;
  }

  if (authState === 'checking') {
    return <RouteFallback />;
  }

  return children;
}
