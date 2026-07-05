import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/renderWithProviders';
import { ThemeToggle } from './ThemeToggle';

describe('ThemeToggle', () => {
  it('renders localized theme radio controls', async () => {
    const { user } = renderWithProviders(<ThemeToggle />);

    expect(screen.getByRole('radiogroup', { name: '主题切换' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: '系统' })).toHaveAttribute('aria-checked', 'true');

    await user.click(screen.getByRole('radio', { name: '暗色' }));

    expect(screen.getByRole('radio', { name: '暗色' })).toHaveAttribute('aria-checked', 'true');
  });

  it('renders English theme labels', () => {
    renderWithProviders(<ThemeToggle />, { locale: 'en-US' });

    expect(screen.getByRole('radiogroup', { name: 'Theme switcher' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Light' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Dark' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'System' })).toBeInTheDocument();
  });
  it('includes dark mode toggle states', () => {
    renderWithProviders(<ThemeToggle />, { locale: 'en-US' });

    expect(screen.getByRole('radio', { name: 'System' })).toHaveClass('dark:bg-blue-950/60', 'dark:text-blue-200');
    expect(screen.getByRole('radio', { name: 'Light' })).toHaveClass('dark:text-gray-400', 'dark:hover:bg-gray-800');
  });
});
