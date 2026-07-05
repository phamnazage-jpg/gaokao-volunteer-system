import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { SubmitButton } from './SubmitButton';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('SubmitButton', () => {
  it('renders the idle label while enabled', () => {
    renderWithProviders(<SubmitButton isSubmitting={false} idleLabel="提交" />);

    const button = screen.getByRole('button', { name: '提交' });
    expect(button).toBeEnabled();
    expect(button).toHaveAttribute('aria-busy', 'false');
  });

  it('locks the button and exposes busy state while submitting', () => {
    renderWithProviders(<SubmitButton isSubmitting idleLabel="提交" />);

    const button = screen.getByRole('button', { name: /提交中/ });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'true');
  });

  it('renders English submitting label', () => {
    renderWithProviders(<SubmitButton isSubmitting idleLabel="Submit" />, { locale: 'en-US' });

    expect(screen.getByRole('button', { name: 'Submitting...' })).toBeDisabled();
  });
});
