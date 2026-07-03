import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'node:path';

// V10 选项 B · Vite 5 + React 19 + Tailwind 4
// 替代 Next.js 16 App Router，使用 React Router 7 (client-side routing)
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    // CloudStudio / WorkBuddy 预览代理白名单
    allowedHosts: [
      'webview.e2b.bj5.sandbox.cloudstudio.club',
      '.sandbox.cloudstudio.club',
      '.cloudstudio.club',
      '.workbuddy.agentos-worker.net',
      '.agentos-worker.net',
      'localhost',
      '127.0.0.1',
    ],
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
    strictPort: true,
  },
  build: {
    target: 'es2022',
    sourcemap: true,
    rollupOptions: {
      output: {
        // V10 优化: 手动 chunk split
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom', 'react-router'],
          'query-vendor': ['@tanstack/react-query', '@tanstack/react-query-devtools'],
          'state-vendor': ['zustand'],
          'form-vendor': ['react-hook-form', '@hookform/resolvers', 'zod'],
          'markdown-vendor': ['react-markdown', 'rehype-sanitize', 'remark-gfm'],
          'chart-vendor': ['recharts'],
          'qrcode-vendor': ['qrcode.react'],
          'icons-vendor': ['lucide-react'],
        },
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
    // 4KB 以下内联
    assetsInlineLimit: 4096,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json'],
      exclude: ['**/node_modules/**', '**/dist/**', '**/*.test.{ts,tsx}', '**/*.spec.{ts,tsx}'],
    },
  },
});
