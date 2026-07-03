/**
 * V10 选项 B · SafeMarkdown 单测 (XSS 防护)
 *
 * 覆盖 V10 不变量 B2
 */
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { SafeMarkdown } from '@/components/shared/SafeMarkdown';

describe('SafeMarkdown (V10 不变量 B2 · XSS 防护)', () => {
  it('过滤 <script> 标签', () => {
    const { container } = render(<SafeMarkdown content="<script>alert(1)</script>hello" />);
    expect(container.querySelector('script')).toBeNull();
    expect(container.innerHTML).not.toMatch(/<script/i);
  });

  it('过滤 javascript: 协议', () => {
    const { container } = render(<SafeMarkdown content="[click](javascript:alert(1))" />);
    const link = container.querySelector('a');
    expect(link?.getAttribute('href') ?? '').not.toMatch(/^javascript:/i);
  });

  it('过滤 onerror 处理器', () => {
    const { container } = render(<SafeMarkdown content='<img src=x onerror="alert(1)">' />);
    expect(container.innerHTML).not.toMatch(/onerror/i);
  });

  it('渲染合法 Markdown: 标题 + 列表 + 代码', () => {
    const md = `# Title
- item 1
- item 2

\`\`\`js
console.log('hi')
\`\`\``;
    const { container } = render(<SafeMarkdown content={md} />);
    expect(container.querySelector('h1')?.textContent).toBe('Title');
    expect(container.querySelectorAll('li')).toHaveLength(2);
    expect(container.querySelector('code')).toBeInTheDocument();
  });

  it('渲染行内代码', () => {
    const { container } = render(<SafeMarkdown content="Use `useState` hook" />);
    const code = container.querySelector('code');
    expect(code?.textContent).toBe('useState');
  });
});