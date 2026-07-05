import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { Dropdown } from './Dropdown';
import { Modal } from './Modal';
import { Tree, type TreeNode } from './Tree';
import { renderWithProviders } from '@/test/renderWithProviders';

const treeNodes: TreeNode[] = [
  {
    id: 'root',
    label: '根节点',
    children: [{ id: 'child', label: '子节点' }],
  },
];

describe('shared component keyboard accessibility', () => {
  it('opens Dropdown with keyboard focus and Enter', async () => {
    const { user } = renderWithProviders(
      <Dropdown
        label="快捷入口"
        items={[
          { href: '/plans', label: '我的方案' },
          { href: '/data-query', label: '数据查询' },
        ]}
      />,
    );

    await user.tab();
    expect(screen.getByRole('button', { name: /快捷入口/ })).toHaveFocus();

    await user.keyboard('{Enter}');

    expect(screen.getByRole('menu', { name: '快捷入口' })).toBeInTheDocument();
  });

  it('keeps Modal focusable and closes with Escape', async () => {
    const onClose = vi.fn();
    const { user } = renderWithProviders(
      <Modal open title="数据查询口径" onClose={onClose}>
        口径内容
      </Modal>,
    );

    expect(screen.getByRole('dialog', { name: '数据查询口径' })).toHaveFocus();

    await user.keyboard('{Escape}');

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('toggles Tree nodes through keyboard activation', async () => {
    const { user } = renderWithProviders(<Tree nodes={treeNodes} label="键盘树" defaultExpandedIds={['root']} />);

    await user.tab();
    expect(screen.getByRole('button', { name: '收起根节点' })).toHaveFocus();

    await user.keyboard('{Enter}');

    expect(screen.queryByText('子节点')).not.toBeInTheDocument();
  });
});
