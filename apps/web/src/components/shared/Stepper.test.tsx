import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { Stepper, type StepperStep } from './Stepper';
import { renderWithProviders } from '@/test/renderWithProviders';

const steps: StepperStep[] = [
  { key: 'province', label: '省份' },
  { key: 'score', label: '分数' },
  { key: 'subjects', label: '位次 / 选科' },
];

describe('Stepper', () => {
  it('marks the current step for assistive tech', () => {
    renderWithProviders(<Stepper steps={steps} currentIndex={1} />);

    expect(screen.getByLabelText('步骤进度')).toHaveAttribute('aria-valuenow', '2');
    expect(screen.getByText('分数')).toHaveAttribute('aria-current', 'step');
  });

  it('renders English default label', () => {
    renderWithProviders(<Stepper steps={steps} currentIndex={0} />, { locale: 'en-US' });

    expect(screen.getByLabelText('Step progress')).toHaveAttribute('aria-valuenow', '1');
  });

  it('clamps out-of-range current index', () => {
    renderWithProviders(<Stepper steps={steps} currentIndex={99} label="表单步骤" />);

    expect(screen.getByLabelText('表单步骤')).toHaveAttribute('aria-valuenow', '3');
    expect(screen.getByText('位次 / 选科')).toHaveAttribute('aria-current', 'step');
  });
  it('includes dark mode stepper state styles', () => {
    renderWithProviders(
      <Stepper
        steps={[
          { key: 'first', label: 'First' },
          { key: 'second', label: 'Second' },
          { key: 'third', label: 'Third' },
        ]}
        currentIndex={1}
      />,
      { locale: 'en-US' },
    );

    expect(screen.getByText('Second')).toHaveClass('dark:text-blue-300');
    expect(screen.getByText('Third')).toHaveClass('dark:text-gray-500');
  });
});
