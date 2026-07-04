/**
 * Sprint 4 T-B-40 · Share Link 状态面板
 */
import { describe, expect, it } from 'vitest';
import { screen, within } from '@testing-library/react';
import { ShareDialogPage } from './ShareDialogPage';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('ShareDialogPage', () => {
  it('renders the latest share-link status panel with real stats', async () => {
    renderWithProviders(<ShareDialogPage />);

    const panel = await screen.findByRole('region', { name: '分享状态面板' });

    expect(within(panel).getByText('ABC123')).toBeInTheDocument();
    expect(within(panel).getByText('https://example.test/s/ABC123')).toBeInTheDocument();
    expect(await within(panel).findByText('12')).toBeInTheDocument();
    expect(within(panel).getByText('5')).toBeInTheDocument();
    expect(within(panel).getByText(/2026\/7\/3/)).toBeInTheDocument();
  });
});
