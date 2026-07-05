import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { Tooltip } from './Tooltip';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('Tooltip', () => {
  it('links trigger to tooltip content for assistive tech', () => {
    renderWithProviders(
      <Tooltip label="用于解释当前字段">
        <button type="button">?</button>
      </Tooltip>,
    );

    const trigger = screen.getByRole('button', { name: '?' });
    const tooltip = screen.getByRole('tooltip');

    expect(trigger.parentElement).toHaveAttribute('aria-describedby', tooltip.id);
    expect(tooltip).toHaveTextContent('用于解释当前字段');
  });
});
