import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // WorkBuddy / CloudStudio / E2B 预览页通常不是 localhost，而是通过外部域名代理到 Next.js dev server。
  // Next.js dev 模式默认会阻止非白名单 origin 访问 /_next/webpack-hmr 等 dev resource，
  // 结果就是页面能打开但客户端 JS / HMR 被拦截，所有交互看起来都“不可用”。
  //
  // 注意：修改该配置后必须彻底重启 next dev；热更新不会重新加载 next.config.ts。
  allowedDevOrigins: [
    'webview.e2b.bj5.sandbox.cloudstudio.club',
    '*.sandbox.cloudstudio.club',
    '*.cloudstudio.club',
    '*.workbuddy.agentos-worker.net',
    '*.agentos-worker.net',
    'localhost',
    '127.0.0.1',
  ],
};

export default nextConfig;
