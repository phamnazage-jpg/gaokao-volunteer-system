/**
 * V10 选项 B · AboutPage
 * 原型帮助页：保留 UI/交互说明与产品可信提示。
 */
import { Link } from 'react-router-dom';

const CAPABILITIES = [
  { icon: '💬', title: 'AI 咨询', desc: '围绕分数、位次、选科和偏好进行连续对话。' },
  { icon: '📋', title: '志愿方案', desc: '按冲刺、稳妥、保底组织候选院校与专业。' },
  { icon: '✅', title: '方案审核', desc: '识别滑档、退档、专业限制等高风险点。' },
  { icon: '📱', title: '移动适配', desc: '保持原型移动端底部 48px Tab 与安全区体验。' },
] as const;

export function AboutPage() {
  return (
    <main className="flex-1 overflow-y-auto px-4 py-6 pb-20 lg:pb-6">
      <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-purple-600 text-xl text-white">
          🎓
        </div>
        <h1 className="mt-4 text-xl font-bold text-gray-900">升学助手</h1>
        <p className="mt-2 text-sm leading-6 text-gray-600">
          V10 前端重构保留原型的 UI 与交互契约，同时使用 Vite、React Router、Zustand 和 TanStack Query 重新实现技术层。
        </p>
      </section>

      <section className="mt-5 grid gap-3 sm:grid-cols-2">
        {CAPABILITIES.map((item) => (
          <article key={item.title} className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
            <div className="text-2xl" aria-hidden="true">{item.icon}</div>
            <h2 className="mt-2 text-sm font-semibold text-gray-900">{item.title}</h2>
            <p className="mt-1 text-xs leading-5 text-gray-500">{item.desc}</p>
          </article>
        ))}
      </section>

      <div className="mt-6 rounded-2xl bg-amber-50 p-4 text-xs leading-5 text-amber-800">
        AI 结果仅作辅助决策，最终志愿填报请以考试院和高校官方信息为准。
      </div>

      <Link to="/" className="mt-6 inline-flex rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
        返回对话
      </Link>
    </main>
  );
}
