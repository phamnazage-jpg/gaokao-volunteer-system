import { useState } from 'react';
import { useIntl } from 'react-intl';

export interface TreeNode {
  id: string;
  label: string;
  description?: string;
  children?: TreeNode[];
}

interface TreeProps {
  nodes: TreeNode[];
  label: string;
  defaultExpandedIds?: string[];
  className?: string;
}

function TreeItem({
  node,
  level,
  expandedIds,
  toggleNode,
}: {
  node: TreeNode;
  level: number;
  expandedIds: Set<string>;
  toggleNode: (id: string) => void;
}) {
  const intl = useIntl();
  const hasChildren = Boolean(node.children?.length);
  const isExpanded = expandedIds.has(node.id);

  return (
    <li role="treeitem" aria-expanded={hasChildren ? isExpanded : undefined} aria-level={level} className="rounded-2xl border border-gray-100 bg-white dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-start gap-3 px-4 py-3">
        {hasChildren ? (
          <button
            type="button"
            className="mt-0.5 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-50 text-blue-700 transition hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-blue-950/60 dark:text-blue-200 dark:hover:bg-blue-900"
            onClick={() => toggleNode(node.id)}
            aria-label={intl.formatMessage({ id: isExpanded ? 'tree.collapse' : 'tree.expand' }, { label: node.label })}
          >
            <span className={`transition-transform ${isExpanded ? 'rotate-90' : ''}`} aria-hidden="true">
              ›
            </span>
          </button>
        ) : (
          <span className="mt-3 h-1.5 w-1.5 shrink-0 rounded-full bg-gray-300 dark:bg-gray-600" aria-hidden="true" />
        )}
        <div className="min-w-0">
          <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">{node.label}</p>
          {node.description && <p className="mt-1 text-xs leading-5 text-gray-500 dark:text-gray-400">{node.description}</p>}
        </div>
      </div>
      {hasChildren && isExpanded && (
        <ul role="group" className="space-y-2 border-t border-gray-100 bg-gray-50/60 p-3 pl-8 dark:border-gray-800 dark:bg-gray-950/60">
          {node.children?.map((child) => (
            <TreeItem key={child.id} node={child} level={level + 1} expandedIds={expandedIds} toggleNode={toggleNode} />
          ))}
        </ul>
      )}
    </li>
  );
}

export function Tree({ nodes, label, defaultExpandedIds = [], className = '' }: TreeProps) {
  const [expandedIds, setExpandedIds] = useState(() => new Set(defaultExpandedIds));
  const toggleNode = (id: string): void => {
    setExpandedIds((current) => {
      const next = new Set(current);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  return (
    <ul role="tree" aria-label={label} className={`space-y-2 ${className}`}>
      {nodes.map((node) => (
        <TreeItem key={node.id} node={node} level={1} expandedIds={expandedIds} toggleNode={toggleNode} />
      ))}
    </ul>
  );
}
