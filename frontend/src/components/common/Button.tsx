import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  className = '',
  ...props
}) => {
  const baseClasses =
    'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed';

  const sizeClasses = {
    sm: 'text-xs px-3 py-1.5 gap-1.5',
    md: 'text-sm px-4 py-2.5 gap-2',
    lg: 'text-base px-5 py-3 gap-2.5',
  }[size];

  const variantClasses = {
    primary:
      'bg-[#C5A059] text-white hover:bg-[#B38E46] active:bg-[#9E7A34] focus:ring-[#C5A059] shadow-sm',
    secondary:
      'bg-[#FAF6F0] text-stone-800 hover:bg-[#F2EAE0] active:bg-[#E8DCCF] border border-[#E5DACB] focus:ring-[#C5A059]',
    outline:
      'bg-transparent text-stone-700 hover:bg-stone-50 border border-stone-200 active:bg-stone-100 focus:ring-stone-400',
    danger:
      'bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 focus:ring-rose-400',
    ghost:
      'bg-transparent text-stone-600 hover:text-stone-900 hover:bg-stone-100/70 focus:ring-stone-300',
  }[variant];

  return (
    <button
      className={`${baseClasses} ${sizeClasses} ${variantClasses} ${className}`}
      {...props}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
    </button>
  );
};
