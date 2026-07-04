/**
 * V10 选项 B · Sidebar 组件 (桌面端 ≥ 1024px 显示)
 *
 * V10 不变量 L1: 桌面端 ≥ 1024px 显示侧栏三栏布局
 *
 * 从 Next.js Link/usePathname 改为 React Router 7 (Vite 友好)
 *
 * T-B-26: hover NavLink 触发 lazy chunk prefetch
 */
import { NavLink } from 'react-router-dom';
import { ThemeToggle } from '@/components/shared/ThemeToggle';
import { usePrefetchLazyRoute } from '@/hooks/usePrefetchLazyRoute';

interface RecentChat {
  id: string;
  title: string;
}

interface Props {
  recentChats: RecentChat[];
  activeChatId?: string;
  onNewChat: () => void;
  onSelectChat: (id: string) => void;
}

interface NavItem {
  to: string;
  label: string;
  icon: string;
}

const NAV_ITEMS: ReadonlyArray<NavItem> = [
  { to: '/', label: '对话', icon: '💬' },
  { to: '/plans', label: '我的方案', icon: '📋' },
  { to: '/consultations', label: '咨询记录', icon: '📖' },
  { to: '/plans/compare', label: '方案对比', icon: '⚖️' },
  { to: '/data-query', label: '数据查询', icon: '📊' },
  { to: '/share', label: '分享', icon: '🔗' },
  { to: '/review', label: '审核', icon: '🛡️' },
  { to: '/poster', label: '海报', icon: '🖼️' },
  { to: '/about', label: '帮助', icon: '❓' },
];

export function Sidebar({ recentChats, activeChatId, onNewChat, onSelectChat }: Props) {
  const prefetch = usePrefetchLazyRoute();
  return (
    <aside className="sidebar hidden lg:flex w-64 shrink-0 flex-col gap-2 border-r border-gray-100 bg-white p-4">
      {/* Logo + ThemeToggle */}
      <div className="flex items-center justify-between mb-2">
        <NavLink to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white text-sm">
            🎓
          </div>
          <span className="text-sm font-bold text-gray-800">升学助手</span>
        </NavLink>
        <ThemeToggle />
      </div>

      {/* 新建对话 */}
      <button
        type="button"
        onClick={onNewChat}
        className="w-full py-2.5 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-1"
      >
        ✨ 新建对话
      </button>

      {/* 导航 */}
      <nav className="flex flex-col gap-0.5" aria-label="主导航">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            onMouseEnter={() => prefetch(item.to)}
            onFocus={() => prefetch(item.to)}
            className={({ isActive }) =>
              `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-600 hover:bg-gray-100'
              }`
            }
          >
            <span aria-hidden="true">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* 最近对话 */}
      {recentChats.length > 0 && (
        <div className="mt-6">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2 px-1">最近对话</h3>
          <div className="flex flex-col gap-0.5">
            {recentChats.slice(0, 10).map((chat) => (
              <button
                key={chat.id}
                type="button"
                onClick={() => onSelectChat(chat.id)}
                className={`text-left px-3 py-2 rounded-lg text-sm truncate transition-colors ${
                  chat.id === activeChatId ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'
                }`}
              >
                {chat.title || '未命名对话'}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 底部信息 */}
      <div className="mt-auto pt-4">
        <p className="text-xs text-gray-400 text-center">AI 辅助决策，请以官方信息为准</p>
      </div>
    </aside>
  );
}