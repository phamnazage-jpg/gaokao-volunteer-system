'use client';

/**
 * 安全的 Markdown 渲染组件
 * 替换当前的 formatMarkdownContent 和 CareerCard 中的 dangerouslySetInnerHTML
 *
 * 依赖: npm install react-markdown rehype-sanitize
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';
import type { Components } from 'react-markdown';

interface Props {
  content: string;
  /** 是否为对话气泡中的内容（使用更紧凑的样式） */
  compact?: boolean;
}

/** 自定义组件渲染（语义化 + 无障碍） */
const components: Components = {
  // 标题层级
  h1: ({ children, ...props }) => (
    <h1 className="text-lg font-bold mb-2 mt-3" {...props}>{children}</h1>
  ),
  h2: ({ children, ...props }) => (
    <h2 className="text-base font-semibold mb-1.5 mt-2" {...props}>{children}</h2>
  ),
  h3: ({ children, ...props }) => (
    <h3 className="text-sm font-semibold mb-1 mt-1.5" {...props}>{children}</h3>
  ),

  // 列表
  ul: ({ children, ...props }) => (
    <ul className="list-disc pl-4 my-1.5 space-y-0.5" {...props}>{children}</ul>
  ),
  ol: ({ children, ...props }) => (
    <ol className="list-decimal pl-4 my-1.5 space-y-0.5" {...props}>{children}</ol>
  ),
  li: ({ children, ...props }) => (
    <li className="text-sm leading-relaxed" {...props}>{children}</li>
  ),

  // 段落
  p: ({ children, ...props }) => (
    <p className="text-sm leading-relaxed mb-1 last:mb-0" {...props}>{children}</p>
  ),

  // 强调
  strong: ({ children, ...props }) => (
    <strong className="font-semibold text-gray-900 dark:text-gray-100" {...props}>{children}</strong>
  ),

  // 行内代码
  code: ({ children, className, ...props }) => {
    const isInline = !className;
    if (isInline) {
      return (
        <code className="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono" {...props}>
          {children}
        </code>
      );
    }
    return <code className={className} {...props}>{children}</code>;
  },

  // 链接
  a: ({ children, href, ...props }) => (
    <a
      href={href}
      className="text-blue-600 dark:text-blue-400 underline hover:no-underline"
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    >
      {children}
    </a>
  ),

  // 分割线
  hr: (props) => <hr className="my-3 border-gray-200 dark:border-gray-700" {...props} />,

  // 引用块
  blockquote: ({ children, ...props }) => (
    <blockquote className="border-l-3 border-blue-400 pl-3 my-2 text-gray-600 dark:text-gray-400 italic" {...props}>
      {children}
    </blockquote>
  ),
};

export function SafeMarkdown({ content, compact = false }: Props) {
  return (
    <div className={compact ? 'prose-compact' : 'prose-sm max-w-none'}>
      <ReactMarkdown
        components={components}
        rehypePlugins={[rehypeSanitize]}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
