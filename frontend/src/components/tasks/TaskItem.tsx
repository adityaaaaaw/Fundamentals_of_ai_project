import React from 'react';
import { Calendar, Check, Trash2, Edit2, Clock } from 'lucide-react';
import type { Task } from '../../types';
import { Badge } from '../common/Badge';
import { usePlanner } from '../../context/PlannerContext';

interface TaskItemProps {
  task: Task;
  onEdit: (task: Task) => void;
}

export const TaskItem: React.FC<TaskItemProps> = ({ task, onEdit }) => {
  const { toggleTaskCompletion, deleteTask } = usePlanner();

  const isCompleted = task.status === 'completed';
  const isMissed = task.status === 'missed';

  // Calculate days until due
  const getDueLabel = (dateStr: string) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const due = new Date(dateStr);
    due.setHours(0, 0, 0, 0);

    const diffTime = due.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return { text: 'Due Today', urgent: true };
    if (diffDays === 1) return { text: 'Due Tomorrow', urgent: false };
    if (diffDays === -1) return { text: '1 day overdue', urgent: true };
    if (diffDays < -1) return { text: `${Math.abs(diffDays)} days overdue`, urgent: true };
    return { text: `Due in ${diffDays} days`, urgent: false };
  };

  const dueInfo = getDueLabel(task.due_date);

  return (
    <div
      className={`group relative bg-white rounded-2xl border transition-all duration-200 p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
        isCompleted
          ? 'border-stone-200/80 bg-stone-50/40 opacity-80'
          : isMissed
          ? 'border-rose-200/90 bg-rose-50/20'
          : 'border-[#EFEAE1] hover:border-[#D9C49A] hover:shadow-soft'
      }`}
    >
      {/* Left section: Checkbox + details */}
      <div className="flex items-start gap-3.5 flex-1 min-w-0">
        <button
          type="button"
          onClick={() => toggleTaskCompletion(task.id)}
          className={`shrink-0 mt-0.5 w-5 h-5 rounded-lg border flex items-center justify-center transition-colors ${
            isCompleted
              ? 'bg-emerald-600 border-emerald-600 text-white'
              : 'border-stone-300 hover:border-[#C5A059] bg-white'
          }`}
          title={isCompleted ? 'Mark as pending' : 'Mark as completed'}
        >
          {isCompleted && <Check className="w-3.5 h-3.5 stroke-[3]" />}
        </button>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            <span className="text-[11px] font-semibold text-[#8B6E30] bg-[#FAF4E6] px-2 py-0.5 rounded-md border border-[#ECDDBF]">
              {task.subject}
            </span>
            <Badge variant="priority" value={task.priority} size="sm" />
            <Badge variant="status" value={task.status} size="sm" />
          </div>

          <h4
            className={`text-sm sm:text-base font-semibold leading-snug break-words ${
              isCompleted ? 'line-through text-stone-400' : 'text-stone-900'
            }`}
          >
            {task.title}
          </h4>

          {task.notes && (
            <p className="text-xs text-stone-500 mt-1 line-clamp-2 leading-relaxed">
              {task.notes}
            </p>
          )}

          {/* Date info */}
          <div className="flex items-center gap-3 mt-2 text-xs text-stone-500">
            <span className="inline-flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-stone-400" />
              {task.due_date}
            </span>

            {!isCompleted && (
              <span
                className={`inline-flex items-center gap-1 font-medium ${
                  dueInfo.urgent ? 'text-rose-600 font-semibold' : 'text-stone-500'
                }`}
              >
                <Clock className="w-3 h-3" />
                {dueInfo.text}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Right section: Action Buttons */}
      <div className="flex items-center justify-end gap-1.5 pt-2 sm:pt-0 border-t sm:border-t-0 border-stone-100">
        <button
          onClick={() => onEdit(task)}
          className="p-1.5 text-stone-400 hover:text-stone-700 hover:bg-stone-100 rounded-lg transition-colors"
          title="Edit task"
        >
          <Edit2 className="w-4 h-4" />
        </button>
        <button
          onClick={() => deleteTask(task.id)}
          className="p-1.5 text-stone-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
          title="Delete task"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
