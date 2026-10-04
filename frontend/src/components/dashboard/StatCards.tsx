import React from 'react';
import { CheckCircle2, Clock, ListTodo, TrendingUp } from 'lucide-react';
import { Card } from '../common/Card';
import { usePlanner } from '../../context/PlannerContext';

export const StatCards: React.FC = () => {
  const { totalTasks, completedTasks, pendingTasks } = usePlanner();

  const completionPercentage = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  const stats = [
    {
      label: 'Total Tasks',
      value: totalTasks,
      subtext: 'Active coursework items',
      icon: ListTodo,
      iconBg: 'bg-[#FAF4E6]',
      iconColor: 'text-[#B08B44]',
      borderColor: 'border-[#EFEAE1]',
    },
    {
      label: 'Completed',
      value: completedTasks,
      subtext: `${completionPercentage}% completion rate`,
      icon: CheckCircle2,
      iconBg: 'bg-emerald-50',
      iconColor: 'text-emerald-600',
      borderColor: 'border-emerald-100',
    },
    {
      label: 'Pending',
      value: pendingTasks,
      subtext: 'Needs attention soon',
      icon: Clock,
      iconBg: 'bg-amber-50',
      iconColor: 'text-amber-600',
      borderColor: 'border-amber-100',
    },
    {
      label: 'Progress Rate',
      value: `${completionPercentage}%`,
      subtext: `${completedTasks} of ${totalTasks} done`,
      icon: TrendingUp,
      iconBg: 'bg-[#FAF3E0]',
      iconColor: 'text-[#C5A059]',
      borderColor: 'border-[#ECD9AF]',
      progressBar: true,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, idx) => {
        const Icon = stat.icon;
        return (
          <Card
            key={idx}
            hoverEffect
            className={`border ${stat.borderColor} relative overflow-hidden flex flex-col justify-between`}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-stone-500">
                  {stat.label}
                </p>
                <h3 className="text-2xl sm:text-3xl font-heading font-bold text-stone-900 mt-1">
                  {stat.value}
                </h3>
              </div>

              <div className={`w-10 h-10 rounded-xl ${stat.iconBg} ${stat.iconColor} flex items-center justify-center shrink-0 shadow-xs`}>
                <Icon className="w-5 h-5" />
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-stone-100">
              <p className="text-xs text-stone-500 font-medium">
                {stat.subtext}
              </p>

              {stat.progressBar && (
                <div className="w-full bg-stone-100 rounded-full h-1.5 mt-2 overflow-hidden">
                  <div
                    className="bg-[#C5A059] h-1.5 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, completionPercentage)}%` }}
                  />
                </div>
              )}
            </div>
          </Card>
        );
      })}
    </div>
  );
};
