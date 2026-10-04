import React from 'react';
import { Clock, CheckCircle2, XCircle, AlertCircle, Edit2, Trash2 } from 'lucide-react';
import type { StudySession, SessionStatus } from '../../types';
import { Badge } from '../common/Badge';
import { usePlanner } from '../../context/PlannerContext';

interface SessionCardProps {
  session: StudySession;
  onEdit: (session: StudySession) => void;
}

export const SessionCard: React.FC<SessionCardProps> = ({ session, onEdit }) => {
  const { setSessionStatus, deleteSession } = usePlanner();

  const handleStatusChange = (newStatus: SessionStatus) => {
    setSessionStatus(session.id, newStatus);
  };

  return (
    <div className="bg-white rounded-2xl border border-[#EFEAE1] hover:border-[#D8C7A3] p-4 sm:p-5 transition-all duration-200 shadow-soft hover:shadow-soft-md flex flex-col justify-between">
      <div>
        {/* Header: Subject & Status */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <span
            className="text-xs font-bold px-2.5 py-1 rounded-lg tracking-wide uppercase"
            style={{
              backgroundColor: '#FAF5EA',
              color: '#8B6A26',
              border: '1px solid #ECD9AF',
            }}
          >
            {session.subject}
          </span>

          <Badge variant="status" value={session.status} size="sm" />
        </div>

        {/* Topic Title */}
        <h4 className="font-heading font-semibold text-stone-900 text-sm sm:text-base leading-snug mb-2">
          {session.topic}
        </h4>

        {/* Time and Duration */}
        <div className="flex items-center gap-3 text-xs text-stone-500 mb-4">
          <div className="inline-flex items-center gap-1.5 font-medium text-stone-700 bg-stone-50 px-2.5 py-1 rounded-md border border-stone-200/60">
            <Clock className="w-3.5 h-3.5 text-[#C5A059]" />
            <span>{session.start_time} – {session.end_time}</span>
          </div>
          <span className="text-stone-400 font-medium">
            {session.duration_minutes} mins
          </span>
        </div>
      </div>

      {/* Footer: Quick status buttons & Actions */}
      <div className="pt-3 border-t border-[#F4ECE1] flex items-center justify-between gap-2">
        {/* Status quick switcher */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => handleStatusChange('completed')}
            className={`p-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1 ${
              session.status === 'completed'
                ? 'bg-emerald-100 text-emerald-800'
                : 'text-stone-400 hover:text-emerald-700 hover:bg-emerald-50'
            }`}
            title="Mark Completed"
          >
            <CheckCircle2 className="w-4 h-4" />
          </button>

          <button
            onClick={() => handleStatusChange('missed')}
            className={`p-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1 ${
              session.status === 'missed'
                ? 'bg-rose-100 text-rose-800'
                : 'text-stone-400 hover:text-rose-700 hover:bg-rose-50'
            }`}
            title="Mark Missed"
          >
            <XCircle className="w-4 h-4" />
          </button>

          <button
            onClick={() => handleStatusChange('upcoming')}
            className={`p-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1 ${
              session.status === 'upcoming'
                ? 'bg-amber-100 text-amber-800'
                : 'text-stone-400 hover:text-amber-700 hover:bg-amber-50'
            }`}
            title="Mark Upcoming"
          >
            <AlertCircle className="w-4 h-4" />
          </button>
        </div>

        {/* Edit & Delete actions */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => onEdit(session)}
            className="p-1.5 text-stone-400 hover:text-stone-700 hover:bg-stone-100 rounded-lg transition-colors"
            title="Edit session"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => deleteSession(session.id)}
            className="p-1.5 text-stone-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
            title="Delete session"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
