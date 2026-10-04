import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Calendar, CheckSquare, Sparkles } from 'lucide-react';
import { usePlanner } from '../../context/PlannerContext';

export const MobileNav: React.FC = () => {
  const { pendingTasks } = usePlanner();

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/schedule', label: 'Schedule', icon: Calendar },
    { to: '/tasks', label: 'Tasks', icon: CheckSquare, badge: pendingTasks > 0 ? pendingTasks : undefined },
    { to: '/assistant', label: 'AI Assist', icon: Sparkles },
  ];

  return (
    <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-[#EFEAE1] px-2 py-2 flex items-center justify-around shadow-soft-lg">
      {navItems.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `relative flex flex-col items-center justify-center py-1 px-3 rounded-xl text-xs font-medium transition-colors ${
                isActive
                  ? 'text-[#A07C2F] font-semibold'
                  : 'text-stone-500 hover:text-stone-900'
              }`
            }
          >
            <div className="relative">
              <Icon className="w-5 h-5 mb-0.5" />
              {item.badge !== undefined && (
                <span className="absolute -top-1 -right-2 px-1.5 py-0.2 text-[9px] font-bold rounded-full bg-[#C5A059] text-white">
                  {item.badge}
                </span>
              )}
            </div>
            <span>{item.label}</span>
          </NavLink>
        );
      })}
    </div>
  );
};
