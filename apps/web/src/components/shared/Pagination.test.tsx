import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { Pagination } from './Pagination';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('Pagination', () => {
  it('does not render when one page is enough', () => {
    renderWithProviders(<Pagination page={1} pageSize={5} totalItems={5} onPageChange={vi.fn()} />);
    expect(screen.queryByRole('navigation', { name: '分页导航' })).not.toBeInTheDocument();
  });

  it('renders range and moves to next page', async () => {
    const onPageChange = vi.fn();
    const { user } = renderWithProviders(<Pagination page={1} pageSize={5} totalItems={12} onPageChange={onPageChange} />);

    expect(screen.getByRole('navigation', { name: '分页导航' })).toHaveTextContent('显示 1-5 / 共 12 条');
    await user.click(screen.getByRole('button', { name: '下一页' }));

    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it('clamps page display to available pages', () => {
    renderWithProviders(<Pagination page={99} pageSize={5} totalItems={12} onPageChange={vi.fn()} />);
    expect(screen.getByText('3 / 3')).toBeInTheDocument();
  });

  it('renders English pagination labels', async () => {
    const onPageChange = vi.fn();
    const { user } = renderWithProviders(<Pagination page={1} pageSize={5} totalItems={12} onPageChange={onPageChange} />, { locale: 'en-US' });

    expect(screen.getByRole('navigation', { name: 'Pagination navigation' })).toHaveTextContent('Showing 1-5 / 12 items');
    await user.click(screen.getByRole('button', { name: 'Next' }));

    expect(onPageChange).toHaveBeenCalledWith(2);
  });
  it('includes dark mode pagination surfaces', () => {
    renderWithProviders(<Pagination page={1} pageSize={5} totalItems={12} onPageChange={vi.fn()} />, { locale: 'en-US' });

    expect(screen.getByRole('navigation', { name: 'Pagination navigation' })).toHaveClass('dark:border-gray-800', 'dark:bg-gray-900');
    expect(screen.getByText('Showing 1-5 / 12 items')).toHaveClass('dark:text-gray-400');
    expect(screen.getByRole('button', { name: 'Previous' })).toHaveClass('dark:border-gray-700', 'dark:text-gray-200');
    expect(screen.getByText('1 / 3')).toHaveClass('dark:text-gray-400');
  });
});
