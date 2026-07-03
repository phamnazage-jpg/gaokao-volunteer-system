import type { FallbackProps } from 'react-error-boundary';
import { AlertTriangle, Home, RotateCcw } from 'lucide-react';
import { Link } from 'react-router-dom';

export function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  const message = error instanceof Error ? error.message : '未知错误';

  return (
    <main role="alert" className="flex min-h-full flex-1 items-center justify-center bg-white px-4 py-10 text-center">
      <section className="w-full max-w-md">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-600">
          <AlertTriangle className="h-6 w-6" aria-hidden="true" />
        </div>
        <h1 className="mt-4 text-xl font-semibold text-gray-900">页面暂时无法显示</h1>
        <p className="mt-2 text-sm leading-6 text-gray-600">当前页面遇到异常，请稍后重试或返回首页。</p>
        <p className="mt-3 break-words rounded bg-gray-50 px-3 py-2 text-xs text-gray-500">{message}</p>
        <div className="mt-6 flex flex-col justify-center gap-2 sm:flex-row">
          <button
            type="button"
            onClick={resetErrorBoundary}
            className="inline-flex h-10 items-center justify-center gap-2 rounded bg-gray-100 px-4 text-sm font-medium text-gray-700 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-300"
          >
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
            重试
          </button>
          <Link
            to="/"
            className="inline-flex h-10 items-center justify-center gap-2 rounded bg-blue-600 px-4 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            <Home className="h-4 w-4" aria-hidden="true" />
            回到首页
          </Link>
        </div>
      </section>
    </main>
  );
}
