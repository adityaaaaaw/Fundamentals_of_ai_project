import React, { useState } from 'react';
import { Plus, RotateCcw, CalendarPlus, GraduationCap } from 'lucide-react';
import { Button } from '../common/Button';
import { usePlanner } from '../../context/PlannerContext';
import { TaskModal } from '../tasks/TaskModal';
import { SessionModal } from '../schedule/SessionModal';

interface HeaderProps {
  title?: string;
  subtitle?: string;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle }) => {
  const { resetToSampleData } = usePlanner();
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [isSessionModalOpen, setIsSessionModalOpen] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const todayFormatted = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
  });

  const handleReset = () => {
    resetToSampleData();
    setShowResetConfirm(false);
  };

  return (
    <>
      <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 mb-6 border-b border-[#EFEAE1]">
        {/* Title & Date */}
        <div>
          <div className="flex items-center gap-2 md:hidden mb-2">
            <div className="w-7 h-7 rounded-lg bg-[#FAF3E0] border border-[#E8D9B5] flex items-center justify-center text-[#C5A059]">
              <GraduationCap className="w-4 h-4 text-[#B08B44]" />
            </div>
            <span className="font-heading font-bold text-sm text-stone-900">Study Planner</span>
          </div>

          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-stone-900 tracking-tight">
            {title || 'Good day, Alex! 👋'}
          </h2>
          <p className="text-xs sm:text-sm text-stone-500 mt-1">
            {subtitle || `Today is ${todayFormatted} • Keep your focus high`}
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 sm:gap-2.5 flex-wrap">
          {/* Reset Demo Data button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowResetConfirm(true)}
            icon={<RotateCcw className="w-3.5 h-3.5 text-stone-500" />}
            title="Reset data to initial demo state"
            className="text-xs"
          >
            Reset Demo
          </Button>

          {/* Quick Add Session */}
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsSessionModalOpen(true)}
            icon={<CalendarPlus className="w-3.5 h-3.5 text-[#B08B44]" />}
            className="text-xs"
          >
            Add Session
          </Button>

          {/* Quick Add Task */}
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsTaskModalOpen(true)}
            icon={<Plus className="w-4 h-4" />}
            className="text-xs shadow-soft"
          >
            New Task
          </Button>
        </div>
      </header>

      {/* Task Modal */}
      <TaskModal
        isOpen={isTaskModalOpen}
        onClose={() => setIsTaskModalOpen(false)}
      />

      {/* Session Modal */}
      <SessionModal
        isOpen={isSessionModalOpen}
        onClose={() => setIsSessionModalOpen(false)}
      />

      {/* Reset Confirmation Dialog */}
      {showResetConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-[#EFEAE1] shadow-soft-lg p-6 max-w-sm w-full animate-in zoom-in-95">
            <h4 className="font-heading font-bold text-base text-stone-900 mb-2">
              Reset Demo Data?
            </h4>
            <p className="text-xs text-stone-600 mb-5 leading-relaxed">
              This will restore all default tasks, study sessions, and exams from the initial demo. Any custom items you created will be reset.
            </p>
            <div className="flex items-center justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowResetConfirm(false)}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={handleReset}
              >
                Yes, Reset
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
