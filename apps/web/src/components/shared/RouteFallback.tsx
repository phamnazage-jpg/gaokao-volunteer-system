/**
 * V10 Sprint 4 · T-B-26 · 路由切换 Suspense fallback
 *
 * 用户点击导航 → lazy chunk 下载期间显示。轻量骨架屏，48px min-height 满足 V10 不变量 L2。
 */
export function RouteFallback() {
  return (
    <div
      role="status"
      aria-label="页面加载中"
      className="flex items-center justify-center min-h-[48px] py-12 text-sm text-gray-500"
    >
      <div className="flex flex-col items-center gap-3">
        <div className="flex gap-1.5" aria-hidden="true">
          <div className="w-2 h-2 bg-gray-300 rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 bg-gray-300 rounded-full animate-pulse" style={{ animationDelay: '120ms' }} />
          <div className="w-2 h-2 bg-gray-300 rounded-full animate-pulse" style={{ animationDelay: '240ms' }} />
        </div>
        <span>加载中…</span>
      </div>
    </div>
  );
}
