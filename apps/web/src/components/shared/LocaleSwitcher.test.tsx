import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { AppIntlProvider } from '@/i18n/AppIntlProvider';
import { LocaleSwitcher } from './LocaleSwitcher';
import { renderWithProviders } from '@/test/renderWithProviders';
import { useUIStore } from '@/stores/ui';

describe('LocaleSwitcher', () => {
  it('switches the active locale from zh-CN to en-US', async () => {
    const { user } = renderWithProviders(
      <AppIntlProvider>
        <LocaleSwitcher />
      </AppIntlProvider>,
    );

    expect(screen.getByLabelText('语言')).toHaveValue('zh-CN');

    await user.selectOptions(screen.getByLabelText('语言'), 'en-US');

    expect(useUIStore.getState().locale).toBe('en-US');
    expect(screen.getByLabelText('Language')).toHaveValue('en-US');
  });
});
