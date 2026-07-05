import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { CardListSkeleton, Skeleton } from './Skeleton';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('Skeleton', () => {
  it('exposes loading status for assistive tech', () => {
    renderWithProviders(<Skeleton />);

    expect(screen.getByRole('status', { name: '内容加载中' })).toBeInTheDocument();
  });

  it('renders a list loading region', () => {
    renderWithProviders(<CardListSkeleton count={2} />);

    expect(screen.getByRole('status', { name: '列表加载中' })).toBeInTheDocument();
    expect(screen.getByRole('status', { name: '列表加载中 1' })).toBeInTheDocument();
    expect(screen.getByRole('status', { name: '列表加载中 2' })).toBeInTheDocument();
  });

  it('renders English defaults', () => {
    renderWithProviders(<CardListSkeleton count={1} />, { locale: 'en-US' });

    expect(screen.getByRole('status', { name: 'List loading' })).toBeInTheDocument();
    expect(screen.getByRole('status', { name: 'List loading 1 metadata' })).toBeInTheDocument();
  });
  it('includes dark mode skeleton surfaces', () => {
    renderWithProviders(<CardListSkeleton count={1} />, { locale: 'en-US' });

    expect(screen.getByRole('status', { name: 'List loading 1' })).toHaveClass('dark:bg-gray-800');
    expect(screen.getByRole('status', { name: 'List loading 1' }).closest('div')).toHaveClass('dark:border-gray-800', 'dark:bg-gray-900');
  });
});
