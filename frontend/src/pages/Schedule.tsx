import React, { useState } from 'react';
import { Plus, Filter, Clock, CalendarDays } from 'lucide-react';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { SessionCard } from '../components/schedule/SessionCard';
import { SessionModal } from '../components/schedule/SessionModal';
import { usePlanner } from '../context/PlannerContext';
import type { DayOfWeek, StudySession, SessionStatus } from '../types';

const DAYS_OF_WEEK: (DayOfWeek | 'All')[] = [
  'All',
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
];

export const Schedule: React.FC = () => {
  const { sessions } = usePlanner();

  const [selectedDay, setSelectedDay] = useState<DayOfWeek | 'All'>('All');
  const [statusFilter, setStatusFilter] = useState<SessionStatus | 'all'>('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [sessionToEdit, setSessionToEdit] = useState<StudySession | null>(null);

  // Filter sessions
  const filteredSessions = sessions.filter((s) => {
    const matchesDay = selectedDay === 'All' || s.day_of_week === selectedDay;
    const matchesStatus = statusFilter === 'all' || s.status === statusFilter;
    return matchesDay && matchesStatus;
  });

  // Calculate day-specific hours
  const totalMinutes = filteredSessions.reduce((acc, s) => acc + (s.duration_minutes || 0), 0);
  const hours = Math.floor(totalMinutes / 60);
  const mins = totalMinutes % 60;

  const handleEdit = (session: StudySession) => {
    setSessionToEdit(session);
    setIsModalOpen(true);
  };

  const handleCreateNew = () => {
    setSessionToEdit(null);
    setIsModalOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#EFEAE1]">
        <div>
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-stone-900 tracking-tight">
            Study Schedule & Timetable
          </h2>
          <p className="text-xs sm:text-sm text-stone-500 mt-1">
            Plan and track weekly subject blocks with automated conflict prevention
          </p>
        </div>

        <Button
          variant="primary"
          onClick={handleCreateNew}
          icon={<Plus className="w-4 h-4" />}
          className="shadow-soft self-start sm:self-auto"
        >
          Add Session
        </Button>
      </div>

      {/* Weekday Selector Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none">
        {DAYS_OF_WEEK.map((day) => {
          const isSelected = selectedDay === day;
          const dayCount = day === 'All'
            ? sessions.length
            : sessions.filter((s) => s.day_of_week === day).length;

          return (
            <button
              key={day}
              onClick={() => setSelectedDay(day)}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-150 flex items-center gap-2 border ${
                isSelected
                  ? 'bg-[#C5A059] text-white border-[#C5A059] shadow-xs'
                  : 'bg-white text-stone-600 border-[#EFEAE1] hover:bg-[#FAF6F0] hover:text-stone-900'
              }`}
            >
              <span>{day}</span>
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                  isSelected ? 'bg-white/25 text-white' : 'bg-stone-100 text-stone-500'
                }`}
              >
                {dayCount}
              </span>
            </button>
          );
        })}
      </div>

      {/* Filters & Metrics Strip */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-white p-3.5 sm:p-4 rounded-2xl border border-[#EFEAE1] shadow-2xs">
        {/* Status filter tabs */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs font-semibold text-stone-400 mr-1 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5" /> Status:
          </span>
          {(['all', 'upcoming', 'completed', 'missed'] as const).map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium capitalize transition-colors ${
                statusFilter === st
                  ? 'bg-[#FAF3E0] text-[#9A7326] font-semibold border border-[#E8D9B5]'
                  : 'text-stone-600 hover:bg-stone-100'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        {/* Time summary */}
        <div className="flex items-center gap-2 text-xs font-medium text-stone-600 self-end sm:self-auto">
          <Clock className="w-3.5 h-3.5 text-[#B08B44]" />
          <span>
            Total Time: <strong className="text-stone-900">{hours}h {mins > 0 ? `${mins}m` : ''}</strong>
          </span>
          <span className="text-stone-300">•</span>
          <span>{filteredSessions.length} session{filteredSessions.length !== 1 ? 's' : ''}</span>
        </div>
      </div>

      {/* Sessions Grid */}
      {filteredSessions.length === 0 ? (
        <Card className="py-14 text-center">
          <div className="w-14 h-14 rounded-2xl bg-[#FAF6F0] border border-[#ECD9AF] text-[#C5A059] flex items-center justify-center mx-auto mb-3">
            <CalendarDays className="w-7 h-7 text-[#B08B44]" />
          </div>
          <h3 className="font-heading font-bold text-base text-stone-900">
            {sessions.length === 0 ? 'No study sessions scheduled.' : 'No Study Sessions Found'}
          </h3>
          <p className="text-xs text-stone-500 mt-1 max-w-sm mx-auto">
            {sessions.length === 0
              ? 'Plan and track your study time by adding your first session.'
              : selectedDay !== 'All'
              ? `No sessions scheduled for ${selectedDay}. Click below to add one.`
              : 'No sessions match your active status filter.'}
          </p>
          <div className="mt-4">
            <Button
              variant="primary"
              size="sm"
              onClick={handleCreateNew}
              icon={<Plus className="w-4 h-4" />}
            >
              Add New Session
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSessions.map((session) => (
            <SessionCard
              key={session.id}
              session={session}
              onEdit={handleEdit}
            />
          ))}
        </div>
      )}

      {/* Add / Edit Session Modal */}
      <SessionModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSessionToEdit(null);
        }}
        sessionToEdit={sessionToEdit}
        defaultDay={selectedDay === 'All' ? 'Monday' : selectedDay}
      />
    </div>
  );
};
