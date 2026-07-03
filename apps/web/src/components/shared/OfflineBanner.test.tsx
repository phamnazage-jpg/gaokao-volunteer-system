import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { OfflineBanner } from './OfflineBanner';

function setNavigatorOnline(value: boolean): void {
  Object.defineProperty(window.navigator, 'onLine', {
    configurable: true,
    value,
  });
}

describe('OfflineBanner', () => {
  afterEach(() => {
    setNavigatorOnline(true);
  });

  it('renders a 48px status banner while offline', () => {
    setNavigatorOnline(false);

    render(<OfflineBanner />);

    const banner = screen.getByRole('status', { name: '离线状态' });
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveClass('min-h-12');
    expect(screen.getByText('当前处于离线状态，写入操作将在恢复联网后自动继续。')).toBeInTheDocument();
  });

  it('does not render while online', () => {
    setNavigatorOnline(true);

    render(<OfflineBanner />);

    expect(screen.queryByRole('status', { name: '离线状态' })).not.toBeInTheDocument();
  });
});
