import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { Dropdown, type DropdownItem } from './Dropdown';
import { renderWithProviders } from '@/test/renderWithProviders';

const items: DropdownItem[] = [
  { href: '/plans', label: '我的方案', description: '继续查看方案' },
  { href: '/data-query', label: '数据查询' },
];

describe('Dropdown', () => {
  it('opens and closes menu items', async () => {
    const { user } = renderWithProviders(<Dropdown label="快捷入口" items={items} />);

    expect(screen.queryByRole('menu', { name: '快捷入口' })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /快捷入口/ }));

    expect(screen.getByRole('menu', { name: '快捷入口' })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: /我的方案/ })).toHaveAttribute('href', '/plans');
  });

  it('closes on Escape', async () => {
    const { user } = renderWithProviders(<Dropdown label="快捷入口" items={items} />);

    await user.click(screen.getByRole('button', { name: /快捷入口/ }));
    await user.keyboard('{Escape}');

    expect(screen.queryByRole('menu', { name: '快捷入口' })).not.toBeInTheDocument();
  });
  it('includes dark mode menu surfaces', async () => {
    const englishItems: DropdownItem[] = [{ href: '/plans', label: 'Plans', description: 'Review plans' }];
    const { user } = renderWithProviders(<Dropdown label="Quick entry" items={englishItems} />);

    const trigger = screen.getByRole('button', { name: /Quick entry/ });
    await user.click(trigger);

    expect(trigger).toHaveClass('dark:text-gray-300', 'dark:hover:bg-gray-800');
    expect(screen.getByRole('menu', { name: 'Quick entry' })).toHaveClass('dark:border-gray-800', 'dark:bg-gray-900');
    expect(screen.getByRole('menuitem', { name: /Plans/ })).toHaveClass('dark:text-gray-200', 'dark:hover:bg-blue-950/40');
    expect(screen.getByText('Review plans')).toHaveClass('dark:text-gray-500');
  });
});
