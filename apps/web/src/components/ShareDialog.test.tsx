/**
 * V10 · Sprint 3 · ShareDialog 单测
 */
import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ShareDialog } from './ShareDialog';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('ShareDialog', () => {
  it('renders nothing when closed', () => {
    renderWithProviders(<ShareDialog planId="p1" planTitle="测试方案" open={false} onClose={() => {}} />);
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('opens and shows create button when open=true', () => {
    renderWithProviders(<ShareDialog planId="p1" planTitle="广东物理 620 方案" open onClose={() => {}} />);
    expect(screen.getByRole('dialog', { name: '分享方案' })).toBeInTheDocument();
    expect(screen.getByText('广东物理 620 方案')).toBeInTheDocument();
  });

  it('closes when X button clicked', async () => {
    const onClose = vi.fn();
    renderWithProviders(<ShareDialog planId="p1" planTitle="测试" open onClose={onClose} />);
    await userEvent.click(screen.getByRole('button', { name: '关闭' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});