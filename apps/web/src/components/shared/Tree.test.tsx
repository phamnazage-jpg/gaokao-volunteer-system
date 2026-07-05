import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { Tree, type TreeNode } from './Tree';
import { renderWithProviders } from '@/test/renderWithProviders';

const nodes: TreeNode[] = [
  {
    id: 'planning',
    label: '志愿规划主链路',
    children: [
      { id: 'chat', label: 'AI 咨询' },
      { id: 'review', label: '方案审核' },
    ],
  },
];

describe('Tree', () => {
  it('renders expanded default nodes', () => {
    renderWithProviders(<Tree nodes={nodes} label="能力地图" defaultExpandedIds={['planning']} />);

    expect(screen.getByRole('tree', { name: '能力地图' })).toBeInTheDocument();
    expect(screen.getByRole('treeitem', { name: /志愿规划主链路/ })).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('AI 咨询')).toBeInTheDocument();
  });

  it('toggles child visibility with localized labels', async () => {
    const { user } = renderWithProviders(<Tree nodes={nodes} label="能力地图" defaultExpandedIds={['planning']} />);

    await user.click(screen.getByRole('button', { name: '收起志愿规划主链路' }));

    expect(screen.queryByText('AI 咨询')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '展开志愿规划主链路' }));

    expect(screen.getByText('方案审核')).toBeInTheDocument();
  });

  it('renders English expand and collapse labels', async () => {
    const { user } = renderWithProviders(<Tree nodes={nodes} label="Capability map" defaultExpandedIds={['planning']} />, { locale: 'en-US' });

    await user.click(screen.getByRole('button', { name: 'Collapse 志愿规划主链路' }));

    expect(screen.getByRole('button', { name: 'Expand 志愿规划主链路' })).toBeInTheDocument();
  });
  it('includes dark mode tree surfaces', () => {
    renderWithProviders(
      <Tree
        nodes={[{ id: 'planning', label: 'Planning', description: 'Plan workflow', children: [{ id: 'chat', label: 'Chat' }] }]}
        label="Capability map"
        defaultExpandedIds={['planning']}
      />,
      { locale: 'en-US' },
    );

    expect(screen.getByRole('treeitem', { name: /Planning/ })).toHaveClass('dark:border-gray-800', 'dark:bg-gray-900');
    expect(screen.getByRole('button', { name: 'Collapse Planning' })).toHaveClass('dark:bg-blue-950/60', 'dark:text-blue-200');
    expect(screen.getByText('Planning')).toHaveClass('dark:text-gray-100');
    expect(screen.getByText('Plan workflow')).toHaveClass('dark:text-gray-400');
    expect(screen.getByRole('group')).toHaveClass('dark:border-gray-800', 'dark:bg-gray-950/60');
  });
});
