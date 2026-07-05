import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/renderWithProviders';
import { RouteFallback } from './RouteFallback';

describe('RouteFallback', () => {
  it('renders localized loading status', () => {
    renderWithProviders(<RouteFallback />);

    expect(screen.getByRole('status', { name: '页面加载中' })).toHaveTextContent('加载中…');
  });

  it('renders English loading status', () => {
    renderWithProviders(<RouteFallback />, { locale: 'en-US' });

    expect(screen.getByRole('status', { name: 'Page loading' })).toHaveTextContent('Loading…');
  });
  it('includes dark mode loading status styles', () => {
    renderWithProviders(<RouteFallback />, { locale: 'en-US' });

    expect(screen.getByRole('status', { name: 'Page loading' })).toHaveClass('dark:text-gray-400');
  });
});
