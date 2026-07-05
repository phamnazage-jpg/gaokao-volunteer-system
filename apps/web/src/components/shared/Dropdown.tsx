import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

export interface DropdownItem {
  label: string;
  href: string;
  description?: string;
}

interface DropdownProps {
  label: string;
  items: DropdownItem[];
  className?: string;
}

export function Dropdown({ label, items, className = '' }: DropdownProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const handlePointerDown = (event: PointerEvent): void => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.key === 'Escape') {
        setOpen(false);
      }
    };

    document.addEventListener('pointerdown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open]);

  return (
    <div ref={rootRef} className={`relative inline-flex ${className}`}>
      <button
        type="button"
        className="inline-flex min-h-[36px] items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-gray-100"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        {label}
        <span className={`transition-transform ${open ? 'rotate-180' : ''}`} aria-hidden="true">
          ⌄
        </span>
      </button>
      {open && (
        <div
          role="menu"
          aria-label={label}
          className="absolute right-0 top-full z-30 mt-2 w-56 overflow-hidden rounded-2xl border border-gray-100 bg-white p-1 shadow-xl dark:border-gray-800 dark:bg-gray-900"
        >
          {items.map((item) => (
            <Link
              key={item.href}
              to={item.href}
              role="menuitem"
              className="block rounded-xl px-3 py-2 text-sm text-gray-700 transition hover:bg-blue-50 hover:text-blue-700 focus:bg-blue-50 focus:text-blue-700 focus:outline-none dark:text-gray-200 dark:hover:bg-blue-950/40 dark:hover:text-blue-200 dark:focus:bg-blue-950/40 dark:focus:text-blue-200"
              onClick={() => setOpen(false)}
            >
              <span className="font-medium">{item.label}</span>
              {item.description && <span className="mt-0.5 block text-xs leading-5 text-gray-400 dark:text-gray-500">{item.description}</span>}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
