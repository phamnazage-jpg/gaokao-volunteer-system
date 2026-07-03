import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { SubmitButton } from './SubmitButton';

describe('SubmitButton', () => {
  it('renders the idle label while enabled', () => {
    render(<SubmitButton isSubmitting={false} idleLabel="提交" submittingLabel="提交中..." />);

    const button = screen.getByRole('button', { name: '提交' });
    expect(button).toBeEnabled();
    expect(button).toHaveAttribute('aria-busy', 'false');
  });

  it('locks the button and exposes busy state while submitting', () => {
    render(<SubmitButton isSubmitting idleLabel="提交" submittingLabel="提交中..." />);

    const button = screen.getByRole('button', { name: /提交中/ });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'true');
  });
});
