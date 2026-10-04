import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Calendar, CheckSquare, Sparkles, BookOpen, GraduationCap } from 'lucide-react';
import { usePlanner } from '../../context/PlannerContext';

export const Sidebar: React.FC = () => {
  const { pendingTasks } = usePlanner();

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/schedule', label: 'Study Schedule', icon: Calendar },
    { to: '/tasks', label: 'My Tasks', icon: CheckSquare, badge: pendingTasks > 0 ? pendingTasks : undefined },
    { to: '/assistant', label: 'AI Assistant', icon: Sparkles, preview: 'Phase 1' },
  ];

  return (
    <aside className="hidden md:flex flex-col w-64 bg-white border-r border-[#EFEAE1] min-h-screen px-4 py-6 justify-between select-none">
      <div>
        {/* Brand / Logo */}
        <div className="flex items-center gap-3 px-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-[#FAF3E0] border border-[#E8D9B5] flex items-center justify-center text-[#C5A059] shadow-soft">
            <GraduationCap className="w-6 h-6 text-[#B08B44]" />
          </div>
          <div>
            <h1 className="font-heading font-bold text-base text-stone-900 leading-tight">
              Study Planner
            </h1>
            <span className="text-[11px] font-medium uppercase tracking-wider text-stone-400">
              AI Student Workspace
            </span>
          </div>
        </div>

        {/* Navigation Section */}
        <div className="space-y-1">
          <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-stone-400">
            Overview & Planning
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all duration-150 ${
                      isActive
                        ? 'bg-[#FDF8EE] text-[#977426] border border-[#ECD9AF] shadow-xs'
                        : 'text-stone-600 hover:text-stone-900 hover:bg-[#FAF6F0]'
                    }`
                  }
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-4 h-4 shrink-0" />
                    <span>{item.label}</span>
                  </div>

                  {item.badge !== undefined && (
                    <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-[#FAF3E0] text-[#9A7326] border border-[#E8D9B5]">
                      {item.badge}
                    </span>
                  )}

                  {item.preview && (
                    <span className="px-1.5 py-0.5 text-[10px] font-medium tracking-wide uppercase rounded-md bg-stone-100 text-stone-500">
                      {item.preview}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Quick Study Tip Card */}
        <div className="mt-8 mx-2 p-3.5 rounded-2xl bg-[#FAF6F0] border border-[#ECE2D2] text-xs text-stone-600">
          <div className="flex items-center gap-2 font-semibold text-stone-800 mb-1">
            <BookOpen className="w-3.5 h-3.5 text-[#C5A059]" />
            <span>Active Recall Tip</span>
          </div>
          <p className="text-[11px] leading-relaxed text-stone-600">
            Space your study intervals and test yourself before reviewing answers for maximum retention.
          </p>
        </div>
      </div>

      {/* User / Workspace Footer */}
      <div className="pt-4 border-t border-[#F4ECE1] px-2">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-[#EADDC5] text-stone-800 flex items-center justify-center font-bold text-xs border border-white shadow-soft">
            AS
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-stone-800 truncate">Aditya Sharma</p>
            <p className="text-[10px] text-stone-500 truncate">Computer Science & AI</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
