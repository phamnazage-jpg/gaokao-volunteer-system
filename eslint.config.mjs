// Flat config (ESLint 9)
import js from '@eslint/js'
import tseslint from 'typescript-eslint'
import reactPlugin from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import jsxA11y from 'eslint-plugin-jsx-a11y'
import nextPlugin from '@next/eslint-plugin-next'

export default [
  {
    ignores: [
      '**/node_modules/**',
      '**/.next/**',
      '**/dist/**',
      '**/build/**',
      '**/coverage/**',
      '**/playwright-report/**',
      '**/test-results/**',
      '**/.turbo/**',
      'admin/**', // 后端 Python 项目，单独有 ruff + mypy
      'data/**',
      'scripts/**',
      'tests/**',
      '前端原型代码/**', // 兼容老路径
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['apps/web/**/*.{ts,tsx}'],
    plugins: {
      react: reactPlugin,
      'react-hooks': reactHooks,
      'jsx-a11y': jsxA11y,
      '@next/next': nextPlugin,
    },
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: 'module',
      globals: {
        React: 'readonly',
        JSX: 'readonly',
      },
    },
    settings: {
      react: { version: '19.0' },
    },
    rules: {
      ...reactPlugin.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      ...jsxA11y.configs.recommended.rules,
      ...nextPlugin.configs.recommended.rules,
      'react/react-in-jsx-scope': 'off', // React 19 自动 JSX runtime
      'react/prop-types': 'off', // 用 TypeScript
      '@typescript-eslint/no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
      // Sprint 1 暂记为 warn（原型 33 个 any 列入 Sprint 2 重构）
      '@typescript-eslint/no-explicit-any': 'warn',
      // React 19 + Next 16 的 setState-in-effect 警告
      'react-hooks/set-state-in-effect': 'warn',
      'no-console': ['warn', { allow: ['warn', 'error', 'info'] }],
    },
  },
]
