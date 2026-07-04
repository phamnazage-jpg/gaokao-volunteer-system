/**
 * V10 · Sprint 3 · StatsCard 单测
 */
import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { StatsCard } from './StatsCard';
import { renderWithProviders } from '@/test/renderWithProviders';
import { server } from '@/test/mocks/server';

describe('StatsCard', () => {
  it('renders 3 stat cards', () => {
    renderWithProviders(<StatsCard code="ABC123" />);
    expect(screen.getByText('访问数')).toBeInTheDocument();
    expect(screen.getByText('独立访客')).toBeInTheDocument();
    expect(screen.getByText('最近访问')).toBeInTheDocument();
  });

  it('has role=list and aria-label', () => {
    renderWithProviders(<StatsCard code="XYZ" />);
    expect(screen.getByRole('list', { name: '分享统计' })).toBeInTheDocument();
  });

  it('shows a fallback when stats are unavailable', async () => {
    server.use(
      http.get('/api/share-link/:code/stats', () => {
        return HttpResponse.json({ message: 'stats unavailable' }, { status: 503 });
      }),
    );

    renderWithProviders(<StatsCard code="ABC123" />);

    expect(await screen.findByRole('status')).toHaveTextContent('统计暂不可用');
  });
});
