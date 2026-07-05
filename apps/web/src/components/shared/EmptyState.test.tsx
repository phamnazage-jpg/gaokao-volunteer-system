import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { EmptyState } from './EmptyState';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('EmptyState', () => {
  it('renders title, description and optional action', () => {
    renderWithProviders(
      <EmptyState title="暂无方案" description="先补充资料生成方案。" actionLabel="开始生成" actionHref="/" />,
    );

    expect(screen.getByRole('heading', { name: '暂无方案' })).toBeInTheDocument();
    expect(screen.getByText('先补充资料生成方案。')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '开始生成' })).toHaveAttribute('href', '/');
  });
  it('includes dark mode empty-state surfaces', () => {
    renderWithProviders(<EmptyState title="No plans yet" description="Generate one to continue." actionLabel="Start" actionHref="/" />);

    expect(screen.getByRole('heading', { name: 'No plans yet' }).closest('section')).toHaveClass(
      'dark:border-blue-900/60',
      'dark:via-gray-900',
    );
    expect(screen.getByRole('heading', { name: 'No plans yet' })).toHaveClass('dark:text-gray-100');
    expect(screen.getByText('Generate one to continue.')).toHaveClass('dark:text-gray-300');
    expect(screen.getByRole('link', { name: 'Start' })).toHaveClass('dark:focus:ring-offset-gray-900');
  });
});
