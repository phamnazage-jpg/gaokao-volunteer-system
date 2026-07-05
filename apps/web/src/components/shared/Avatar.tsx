import { useIntl } from 'react-intl';

interface AvatarProps {
  name: string;
  src?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeClass = {
  sm: 'h-8 w-8 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-12 w-12 text-base',
} as const;

function getInitials(name: string): string {
  const normalized = name.trim();
  if (!normalized) return '?';
  const asciiParts = normalized.split(/\s+/).filter(Boolean);
  if (asciiParts.length >= 2) {
    return `${asciiParts[0]?.[0] ?? ''}${asciiParts[1]?.[0] ?? ''}`.toUpperCase();
  }
  return Array.from(normalized).slice(0, 2).join('').toUpperCase();
}

export function Avatar({ name, src, size = 'md', className = '' }: AvatarProps) {
  const intl = useIntl();
  const initials = getInitials(name);

  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-gradient-to-br from-blue-600 to-cyan-500 font-semibold text-white shadow-sm ${sizeClass[size]} ${className}`}
      aria-label={intl.formatMessage({ id: 'avatar.ariaLabel' }, { name })}
      role="img"
    >
      {src ? <img src={src} alt="" className="h-full w-full object-cover" /> : initials}
    </span>
  );
}
