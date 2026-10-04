import React from 'react';
import { BarChart3, Target, Flame } from 'lucide-react';
import { Card } from '../common/Card';
import { usePlanner } from '../../context/PlannerContext';

export const ProgressChart: React.FC = () => {
  const { weeklyMetrics } = usePlanner();

  const totalStudied = weeklyMetrics.reduce((acc, m) => acc + m.studiedHours, 0);
  const totalTarget = weeklyMetrics.reduce((acc, m) => acc + m.targetHours, 0);
  const maxHours = Math.max(...weeklyMetrics.map((m) => Math.max(m.studiedHours, m.targetHours)), 6);

  return (
    <Card className="flex flex-col justify-between h-full">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#F4ECE1]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#FAF4E6] flex items-center justify-center text-[#B08B44]">
              <BarChart3 className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-heading font-bold text-base text-stone-900">
                Weekly Study Progress
              </h3>
              <p className="text-xs text-stone-500">
                Logged study hours vs. scheduled target
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <div className="flex items-center gap-1.5 font-medium text-stone-600">
              <span className="w-3 h-3 rounded-sm bg-[#C5A059]" />
              <span>Studied</span>
            </div>
            <div className="flex items-center gap-1.5 font-medium text-stone-400">
              <span className="w-3 h-3 rounded-sm bg-stone-200" />
              <span>Target</span>
            </div>
          </div>
        </div>

        {/* Empty state notice if 0 study hours logged */}
        {totalStudied === 0 && (
          <div className="py-2 text-center text-xs text-stone-500 mb-1">
            Your progress will appear here once you start completing tasks.
          </div>
        )}

        {/* Bar Chart Visualization */}
        <div className="pt-2 pb-1">
          <div className="h-44 flex items-end justify-between gap-2 sm:gap-4 px-2">
            {weeklyMetrics.map((item, idx) => {
              const studiedHeightPercent = Math.min(100, Math.round((item.studiedHours / maxHours) * 100));
              const targetHeightPercent = Math.min(100, Math.round((item.targetHours / maxHours) * 100));
              const isGoalMet = item.studiedHours >= item.targetHours && item.studiedHours > 0;

              return (
                <div key={idx} className="flex-1 flex flex-col items-center h-full justify-end group">
                  {/* Tooltip on hover */}
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute -translate-y-28 bg-stone-900 text-white text-[11px] py-1 px-2 rounded-lg pointer-events-none z-20 whitespace-nowrap shadow-md">
                    <p className="font-semibold">{item.fullDay}</p>
                    <p>Studied: {item.studiedHours}h / Goal: {item.targetHours}h</p>
                  </div>

                  {/* Bars Container */}
                  <div className="w-full max-w-[28px] flex items-end justify-center gap-1 h-32 relative">
                    {/* Target ghost bar */}
                    <div
                      className="w-2.5 sm:w-3 bg-stone-200/80 rounded-t-md transition-all duration-300"
                      style={{ height: `${targetHeightPercent}%` }}
                      title={`Target: ${item.targetHours}h`}
                    />

                    {/* Studied filled bar */}
                    <div
                      className={`w-2.5 sm:w-3 rounded-t-md transition-all duration-500 ${
                        item.studiedHours === 0
                          ? 'bg-stone-200/40'
                          : isGoalMet
                          ? 'bg-[#C5A059] group-hover:bg-[#B08B44]'
                          : 'bg-[#D9C28F] group-hover:bg-[#C5A059]'
                      }`}
                      style={{ height: `${item.studiedHours === 0 ? 4 : studiedHeightPercent}%` }}
                      title={`Studied: ${item.studiedHours}h`}
                    />
                  </div>

                  {/* Day label */}
                  <span className="text-[11px] font-semibold text-stone-500 mt-2">
                    {item.day}
                  </span>
                  <span className="text-[10px] text-stone-400 font-mono">
                    {item.studiedHours}h
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Summary Footer */}
      <div className="mt-4 pt-3 border-t border-[#F4ECE1] flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 text-stone-600">
          <Target className="w-3.5 h-3.5 text-[#B08B44]" />
          <span>Total: <strong className="text-stone-900">{totalStudied.toFixed(1)} hrs</strong> of {totalTarget.toFixed(1)} hrs target</span>
        </div>

        <div className="flex items-center gap-1 text-[#9A7426] font-semibold">
          <Flame className={`w-3.5 h-3.5 ${totalStudied > 0 ? 'text-amber-500' : 'text-stone-300'}`} />
          <span>{totalStudied > 0 ? 'Study Streak Active 🔥' : 'No active streak'}</span>
        </div>
      </div>
    </Card>
  );
};
