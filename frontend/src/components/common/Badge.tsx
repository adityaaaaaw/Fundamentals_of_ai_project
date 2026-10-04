import React from 'react';
import type { Priority, TaskStatus, SessionStatus } from '../../types';

interface BadgeProps {
  label?: string;
  variant?: 'priority' | 'status' | 'neutral' | 'gold';
  value?: Priority | TaskStatus | SessionStatus | string;
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  label,
  variant = 'neutral',
  value,
  size = 'md',
  className = '',
}) => {
  const displayLabel = label || (value ? String(value).toUpperCase() : '');

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-medium';

  let colorClasses = 'bg-stone-100 text-stone-700 border-stone-200';

  if (variant === 'priority' || value === 'high' || value === 'medium' || value === 'low') {
    switch (value) {
      case 'high':
        colorClasses = 'bg-rose-50 text-rose-700 border-rose-200';
        break;
      case 'medium':
        colorClasses = 'bg-amber-50 text-amber-800 border-amber-200';
        break;
      case 'low':
        colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200';
        break;
    }
  } else if (variant === 'status' || value === 'completed' || value === 'pending' || value === 'missed' || value === 'upcoming') {
    switch (value) {
      case 'completed':
        colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200';
        break;
      case 'pending':
        colorClasses = 'bg-amber-50 text-amber-800 border-amber-200';
        break;
      case 'upcoming':
        colorClasses = 'bg-sky-50 text-sky-800 border-sky-200';
        break;
      case 'missed':
        colorClasses = 'bg-rose-50 text-rose-700 border-rose-200';
        break;
    }
  } else if (variant === 'gold') {
    colorClasses = 'bg-[#FAF3E0] text-[#9A7326] border-[#E8D9B5]';
  }

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border tracking-wide uppercase font-semibold ${sizeClasses} ${colorClasses} ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70"></span>
      {displayLabel}
    </span>
  );
};
