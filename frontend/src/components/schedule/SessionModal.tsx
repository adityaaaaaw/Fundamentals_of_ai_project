import React, { useState, useEffect } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import type { StudySession, DayOfWeek, SessionStatus } from '../../types';
import { usePlanner } from '../../context/PlannerContext';
import { AlertCircle } from 'lucide-react';

interface SessionModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionToEdit?: StudySession | null;
  defaultDay?: DayOfWeek;
}

const DAYS_OF_WEEK: DayOfWeek[] = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
];

const COMMON_SUBJECTS = [
  'Fundamentals of AI',
  'Linear Algebra',
  'Database Systems',
  'Operating Systems',
  'Data Structures',
  'Computer Networks',
];

const SUBJECT_COLORS: Record<string, string> = {
  'Fundamentals of AI': '#C5A059',
  'Linear Algebra': '#8A7B66',
  'Database Systems': '#5B7A8C',
  'Operating Systems': '#6B8E23',
  'Data Structures': '#C5A059',
};

export const SessionModal: React.FC<SessionModalProps> = ({
  isOpen,
  onClose,
  sessionToEdit,
  defaultDay = 'Monday',
}) => {
  const { addSession, updateSession } = usePlanner();

  const [subject, setSubject] = useState(COMMON_SUBJECTS[0]);
  const [date, setDate] = useState('');
  const [dayOfWeek, setDayOfWeek] = useState<DayOfWeek>(defaultDay);
  const [startTime, setStartTime] = useState('10:00');
  const [endTime, setEndTime] = useState('11:30');
  const [topic, setTopic] = useState('');
  const [status, setStatus] = useState<SessionStatus>('upcoming');
  const [error, setError] = useState<string | null>(null);

  // Compute day of week from date selection
  const handleDateChange = (val: string) => {
    setDate(val);
    if (val) {
      try {
        const d = new Date(val + 'T00:00:00');
        const dayNames: DayOfWeek[] = [
          'Sunday',
          'Monday',
          'Tuesday',
          'Wednesday',
          'Thursday',
          'Friday',
          'Saturday',
        ];
        const day = dayNames[d.getDay()];
        if (day) setDayOfWeek(day);
      } catch {
        // Fallback keep existing
      }
    }
  };

  useEffect(() => {
    if (sessionToEdit) {
      setSubject(sessionToEdit.subject);
      setDate(sessionToEdit.date);
      setDayOfWeek(sessionToEdit.day_of_week);
      setStartTime(sessionToEdit.start_time);
      setEndTime(sessionToEdit.end_time);
      setTopic(sessionToEdit.topic);
      setStatus(sessionToEdit.status);
    } else {
      setSubject(COMMON_SUBJECTS[0]);
      const todayStr = new Date().toISOString().split('T')[0];
      setDate(todayStr);
      setDayOfWeek(defaultDay);
      setStartTime('10:00');
      setEndTime('11:30');
      setTopic('');
      setStatus('upcoming');
    }
    setError(null);
  }, [sessionToEdit, isOpen, defaultDay]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!subject.trim()) {
      setError('Please specify a subject.');
      return;
    }
    if (!topic.trim()) {
      setError('Please provide a topic or study objective.');
      return;
    }
    if (!startTime || !endTime) {
      setError('Please enter both start and end times.');
      return;
    }

    const assignedColor = SUBJECT_COLORS[subject] || '#C5A059';

    if (sessionToEdit) {
      const result = await updateSession(sessionToEdit.id, {
        subject: subject.trim(),
        date,
        day_of_week: dayOfWeek,
        start_time: startTime,
        end_time: endTime,
        topic: topic.trim(),
        status,
        color: assignedColor,
      });

      if (!result.success) {
        setError(result.error || 'Failed to update session.');
        return;
      }
    } else {
      const result = await addSession({
        subject: subject.trim(),
        date: date || new Date().toISOString().split('T')[0],
        day_of_week: dayOfWeek,
        start_time: startTime,
        end_time: endTime,
        duration_minutes: 0, // Auto-computed in context
        topic: topic.trim(),
        status,
        color: assignedColor,
      });

      if (!result.success) {
        setError(result.error || 'Failed to add session.');
        return;
      }
    }

    onClose();
  };


  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={sessionToEdit ? 'Edit Study Session' : 'Schedule Study Session'}
      subtitle="Allocate focused study time with overlap conflict detection"
      maxWidth="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Subject */}
        <div>
          <label className="block text-xs font-semibold text-stone-700 mb-1.5">
            Subject <span className="text-rose-500">*</span>
          </label>
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
        </div>

        {/* Topic / Objective */}
        <div>
          <label className="block text-xs font-semibold text-stone-700 mb-1.5">
            Focus Topic / Objectives <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. Heuristic Search & Minimax Trees"
            className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white"
          />
        </div>

        {/* Date & Day of Week */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1.5">
              Date <span className="text-rose-500">*</span>
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => handleDateChange(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-sm text-stone-900 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1.5">
              Day of Week
            </label>
            <select
              value={dayOfWeek}
              onChange={(e) => setDayOfWeek(e.target.value as DayOfWeek)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-sm text-stone-900 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white"
            >
              {DAYS_OF_WEEK.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Start Time & End Time */}
        <div className="grid grid-cols-2 gap-3.5">
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1.5">
              Start Time <span className="text-rose-500">*</span>
            </label>
            <input
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-sm text-stone-900 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1.5">
              End Time <span className="text-rose-500">*</span>
            </label>
            <input
              type="time"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-sm text-stone-900 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white"
            />
          </div>
        </div>

        {/* Status (if editing) */}
        {sessionToEdit && (
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1.5">
              Session Status
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as SessionStatus)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-sm text-stone-900 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white"
            >
              <option value="upcoming">Upcoming</option>
              <option value="completed">Completed</option>
              <option value="missed">Missed</option>
            </select>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-stone-100">
          <Button type="button" variant="outline" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" size="sm">
            {sessionToEdit ? 'Save Changes' : 'Schedule Session'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
