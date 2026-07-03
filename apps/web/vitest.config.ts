import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';
import path from 'node:path';

// Vitest 独立配置 (与 Vite 共享 resolve.alias 和 plugin)
// 之所以独立：vitest 用 defineConfig from 'vitest/config' 读取 test 字段
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['**/node_modules/**', '**/dist/**', '**/e2e/**'],
  },
});
