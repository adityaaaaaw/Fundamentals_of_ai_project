import React, { useState, useEffect } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import type { Task, Priority, TaskStatus } from '../../types';
import { usePlanner } from '../../context/PlannerContext';

interface TaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  taskToEdit?: Task | null;
}

const COMMON_SUBJECTS = [
  'Fundamentals of AI',
  'Linear Algebra',
  'Database Systems',
  'Operating Systems',
  'Data Structures',
  'Computer Networks',
  'Software Engineering',
];

export const TaskModal: React.FC<TaskModalProps> = ({
  isOpen,
  onClose,
  taskToEdit,
}) => {
  const { addTask, updateTask } = usePlanner();

  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState(COMMON_SUBJECTS[0]);
  const [customSubject, setCustomSubject] = useState('');
  const [isCustomSubject, setIsCustomSubject] = useState(false);
  const [dueDate, setDueDate] = useState('');
  const [priority, setPriority] = useState<Priority>('medium');
  const [status, setStatus] = useState<TaskStatus>('pending');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (taskToEdit) {
      setTitle(taskToEdit.title);
      if (COMMON_SUBJECTS.includes(taskToEdit.subject)) {
        setSubject(taskToEdit.subject);
        setIsCustomSubject(false);
        setCustomSubject('');
      } else {
        setIsCustomSubject(true);
        setCustomSubject(taskToEdit.subject);
      }
      setDueDate(taskToEdit.due_date);
      setPriority(taskToEdit.priority);
      setStatus(taskToEdit.status);
      setNotes(taskToEdit.notes || '');
    } else {
      // Default new task
      setTitle('');
      setSubject(COMMON_SUBJECTS[0]);
      setIsCustomSubject(false);
      setCustomSubject('');
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      setDueDate(tomorrow.toISOString().split('T')[0]);
      setPriority('medium');
      setStatus('pending');
      setNotes('');
    }
    setError(null);
  }, [taskToEdit, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) {
      setError('Please provide a task title.');
      return;
    }

    const finalSubject = isCustomSubject ? customSubject.trim() : subject;
    if (!finalSubject) {
      setError('Please select or specify a subject.');
      return;
    }

    if (!dueDate) {
      setError('Please select a due date.');
      return;
    }

    if (taskToEdit) {
      const res = await updateTask(taskToEdit.id, {
        title: title.trim(),
        subject: finalSubject,
        due_date: dueDate,
        priority,
        status,
        notes: notes.trim() || undefined,
      });
      if (!res.success) {
        setError(res.error || 'Failed to update task.');
        return;
      }
    } else {
      const res = await addTask({
        title: title.trim(),
        subject: finalSubject,
        due_date: dueDate,
        priority,
        status,
        notes: notes.trim() || undefined,
      });
      if (!res.success) {
        setError(res.error || 'Failed to create task.');
        return;
      }
    }

    onClose();
  };


  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={taskToEdit ? 'Edit Task' : 'Create New Task'}
      subtitle={taskToEdit ? 'Update details and deadline' : 'Add a learning task to stay on track'}
      maxWidth="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
            {error}
          </div>
        )}

        {/* Title */}
        <div>
          <label className="block text-xs font-semibold text-stone-700 mb-1.5">
            Task Title <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Implement A* Search Algorithm"
            className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white transition-all"
            autoFocus
          />
        </div>

        {/* Subject */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-semibold text-stone-700">
              Subject <span className="text-rose-500">*</span>
            </label>
            <button
              type="button"
              onClick={() => setIsCustomSubject(!isCustomSubject)}
              className="text-xs text-[#9B762A] hover:underline font-medium"
            >
              {isCustomSubject ? 'Choose from list' : '+ Custom subject'}
            </button>
          </div>

          {isCustomSubject ? (
            <input
              type="text"
              value={customSubject}
              onChange={(e) => setCustomSubject(e.target.value)}
              placeholder="e.g. Cognitive Psychology"
              className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white"
            />
          ) : (
            <select
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-sm text-stone-900 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white"
            >
              {COMMON_SUBJECTS.map((sub) => (
                <option key={sub} value={sub}>
                  {sub}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Due Date & Priority Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1.5">
              Deadline <span className="text-rose-500">*</span>
            </label>
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-sm text-stone-900 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1.5">
              Priority
            </label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as Priority)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-sm text-stone-900 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white"
            >
              <option value="low">Low Priority</option>
              <option value="medium">Medium Priority</option>
              <option value="high">High Priority</option>
            </select>
          </div>
        </div>

        {/* Status (if editing) */}
        {taskToEdit && (
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1.5">
              Status
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as TaskStatus)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-sm text-stone-900 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white"
            >
              <option value="pending">Pending</option>
              <option value="completed">Completed</option>
              <option value="missed">Missed</option>
            </select>
          </div>
        )}

        {/* Notes */}
        <div>
          <label className="block text-xs font-semibold text-stone-700 mb-1.5">
            Notes & Details (Optional)
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={2}
            placeholder="Add relevant instructions, links, or exercise numbers..."
            className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white resize-none"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-stone-100">
          <Button type="button" variant="outline" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" size="sm">
            {taskToEdit ? 'Save Changes' : 'Create Task'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
