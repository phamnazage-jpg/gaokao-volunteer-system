import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { Avatar } from './Avatar';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('Avatar', () => {
  it('renders initials for Chinese names', () => {
    renderWithProviders(<Avatar name="咨询记录" />);

    expect(screen.getByRole('img', { name: '咨询记录 头像' })).toHaveTextContent('咨询');
  });

  it('renders initials for latin names with English accessible label', () => {
    renderWithProviders(<Avatar name="Michael Williams" />, { locale: 'en-US' });

    expect(screen.getByRole('img', { name: 'Michael Williams avatar' })).toHaveTextContent('MW');
  });

  it('renders image without duplicating accessible name', () => {
    renderWithProviders(<Avatar name="用户头像" src="/avatar.png" />);

    expect(screen.getByRole('img', { name: '用户头像 头像' })).toBeInTheDocument();
    expect(screen.getByRole('img', { name: '用户头像 头像' }).querySelector('img')).toHaveAttribute('alt', '');
  });
});
