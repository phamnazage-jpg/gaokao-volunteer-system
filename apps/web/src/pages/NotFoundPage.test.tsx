import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('NotFoundPage i18n', () => {
  it('renders the localized fallback route in Chinese', () => {
    renderWithProviders(<NotFoundPage />);

    expect(screen.getByRole('heading', { name: '页面不存在' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '回到首页' })).toHaveAttribute('href', '/');
  });

  it('renders the localized fallback route in English', () => {
    renderWithProviders(<NotFoundPage />, { locale: 'en-US' });

    expect(screen.getByRole('heading', { name: 'Page not found' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back home' })).toHaveAttribute('href', '/');
  });
  it('includes dark mode not-found copy styles', () => {
    renderWithProviders(<NotFoundPage />, { locale: 'en-US' });

    expect(screen.getByRole('heading', { name: 'Page not found' })).toHaveClass('dark:text-gray-100');
    expect(screen.getByText('The page you visited is not connected yet or has moved. Return to chat to continue using Gaokao Assistant.')).toHaveClass('dark:text-gray-400');
  });
});
