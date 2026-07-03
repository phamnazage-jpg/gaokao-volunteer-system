import type { Metadata, Viewport } from 'next';
import './globals.css';
import { initThemeScript } from '@/lib/theme';

export const metadata: Metadata = {
  title: '升学助手 - AI志愿规划师',
  description: '基于大模型的职业解读与志愿填报智能助手',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <head>
        {/* 主题初始化 — 阻塞渲染，防止暗色模式闪白 */}
        <script dangerouslySetInnerHTML={{ __html: initThemeScript() }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
