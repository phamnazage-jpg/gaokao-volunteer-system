/** V10 选项 B · NotFoundPage */
import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-4 text-center">
      <div className="text-5xl" aria-hidden="true">🧭</div>
      <h1 className="mt-4 text-xl font-bold text-gray-900">页面不存在</h1>
      <p className="mt-2 max-w-sm text-sm text-gray-500">你访问的页面尚未接入或已经移动。可以回到对话页继续使用升学助手。</p>
      <Link to="/" className="mt-6 rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
        回到首页
      </Link>
    </main>
  );
}
