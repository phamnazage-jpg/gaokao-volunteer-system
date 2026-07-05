import { useState } from 'react';
import { useIntl } from 'react-intl';

export interface AccordionItem {
  id: string;
  title: string;
  content: string;
}

interface AccordionProps {
  items: AccordionItem[];
  defaultOpenId?: string;
  label?: string;
  className?: string;
}

export function Accordion({ items, defaultOpenId, label, className = '' }: AccordionProps) {
  const intl = useIntl();
  const [openId, setOpenId] = useState<string | null>(defaultOpenId ?? items[0]?.id ?? null);
  const resolvedLabel = label ?? intl.formatMessage({ id: 'accordion.ariaLabel' });

  return (
    <div className={`space-y-2 ${className}`} aria-label={resolvedLabel}>
      {items.map((item) => {
        const isOpen = openId === item.id;
        const panelId = `${item.id}-panel`;
        const buttonId = `${item.id}-button`;

        return (
          <section key={item.id} className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
            <h3>
              <button
                id={buttonId}
                type="button"
                className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left text-sm font-semibold text-gray-900 transition hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset dark:text-gray-100 dark:hover:bg-gray-800"
                aria-expanded={isOpen}
                aria-controls={panelId}
                onClick={() => setOpenId(isOpen ? null : item.id)}
              >
                <span>{item.title}</span>
                <span className={`text-gray-400 transition-transform dark:text-gray-500 ${isOpen ? 'rotate-180' : ''}`} aria-hidden="true">
                  ⌄
                </span>
              </button>
            </h3>
            {isOpen && (
              <div id={panelId} role="region" aria-labelledby={buttonId} className="border-t border-gray-100 px-4 py-3 text-sm leading-6 text-gray-600 dark:border-gray-800 dark:text-gray-300">
                {item.content}
              </div>
            )}
          </section>
        );
      })}
    </div>
  );
}
