import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
}

export const Card: React.FC<CardProps> = ({ 
  children, 
  className = '', 
  hoverEffect = false,
  ...props 
}) => {
  return (
    <div
      className={`bg-white rounded-2xl border border-[#EFEAE1] shadow-soft p-5 sm:p-6 transition-all duration-200 ${
        hoverEffect ? 'hover:shadow-soft-md hover:border-[#DFC790]' : ''
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
