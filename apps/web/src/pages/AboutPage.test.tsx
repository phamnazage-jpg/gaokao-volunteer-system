import { describe, expect, it } from 'vitest';
import { screen, within } from '@testing-library/react';
import { AboutPage } from './AboutPage';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('AboutPage', () => {
  it('renders FAQ accordion with official-source guidance', async () => {
    const { user } = renderWithProviders(<AboutPage />);

    expect(screen.getByRole('heading', { name: '常见问题' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'AI 结果可以直接作为最终填报依据吗？' }));

    expect(screen.getByRole('region', { name: 'AI 结果可以直接作为最终填报依据吗？' })).toHaveTextContent('最终填报仍需以考试院');
  });

  it('renders capability tree map', () => {
    renderWithProviders(<AboutPage />);

    const capabilityTree = screen.getByRole('tree', { name: '升学助手能力地图' });
    expect(capabilityTree).toBeInTheDocument();
    expect(screen.getByText('志愿规划主链路')).toBeInTheDocument();
    expect(within(capabilityTree).getByText('方案审核')).toBeInTheDocument();
  });

  it('renders English messages when locale switches', () => {
    renderWithProviders(<AboutPage />, { locale: 'en-US' });

    expect(screen.getByRole('heading', { name: 'Gaokao Assistant' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'FAQ' })).toBeInTheDocument();
    expect(screen.getByRole('tree', { name: 'Gaokao Assistant capability map' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back to chat' })).toBeInTheDocument();
  });
  it('includes dark mode page surfaces', () => {
    renderWithProviders(<AboutPage />, { locale: 'en-US' });

    expect(screen.getByRole('heading', { name: 'Gaokao Assistant' }).closest('section')).toHaveClass('dark:border-gray-800', 'dark:bg-gray-900');
    expect(screen.getByRole('heading', { name: 'Gaokao Assistant' })).toHaveClass('dark:text-gray-100');
    expect(screen.getByText('The V10 frontend refactor preserves the prototype UI and interaction contracts while rebuilding the technical layer with Vite, React Router, Zustand, and TanStack Query.')).toHaveClass('dark:text-gray-300');
    expect(screen.getByRole('heading', { name: 'FAQ' })).toHaveClass('dark:text-gray-100');
  });
});
