import React from 'react';
import { Link } from 'react-router-dom';
import { Clock, CheckCircle2, ArrowRight, Calendar } from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { usePlanner } from '../../context/PlannerContext';

export const TodaySessions: React.FC = () => {
  const { todaySessions, setSessionStatus } = usePlanner();

  return (
    <Card className="flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#F4ECE1]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#FAF4E6] flex items-center justify-center text-[#B08B44]">
              <Calendar className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-heading font-bold text-base text-stone-900">
                Today's Study Sessions
              </h3>
              <p className="text-xs text-stone-500">
                {todaySessions.length} session{todaySessions.length !== 1 ? 's' : ''} planned for today
              </p>
            </div>
          </div>

          <Link
            to="/schedule"
            className="inline-flex items-center gap-1 text-xs font-semibold text-[#9A7426] hover:text-[#7A5918] transition-colors"
          >
            <span>Full Schedule</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {todaySessions.length === 0 ? (
          <div className="py-8 text-center">
            <div className="w-12 h-12 rounded-full bg-stone-100 flex items-center justify-center mx-auto mb-2 text-stone-400">
              <Calendar className="w-6 h-6" />
            </div>
            <p className="text-xs font-medium text-stone-600">
              No study sessions scheduled.
            </p>
            <Link
              to="/schedule"
              className="text-xs font-semibold text-[#C5A059] hover:underline mt-1 inline-block"
            >
              Add a session
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {todaySessions.map((session) => {
              const isCompleted = session.status === 'completed';
              return (
                <div
                  key={session.id}
                  className={`p-3.5 rounded-xl border transition-all duration-150 flex items-center justify-between gap-3 ${
                    isCompleted
                      ? 'bg-stone-50/70 border-stone-200/70 opacity-75'
                      : 'bg-white border-[#EFEAE1] hover:border-[#DFC790] shadow-2xs'
                  }`}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[11px] font-semibold text-[#8B6E30] bg-[#FAF4E6] px-2 py-0.5 rounded-md border border-[#ECDDBF]">
                        {session.subject}
                      </span>
                      <Badge variant="status" value={session.status} size="sm" />
                    </div>

                    <p
                      className={`text-xs sm:text-sm font-semibold truncate ${
                        isCompleted ? 'line-through text-stone-400' : 'text-stone-900'
                      }`}
                    >
                      {session.topic}
                    </p>

                    <div className="flex items-center gap-2 mt-1 text-[11px] text-stone-500">
                      <Clock className="w-3 h-3 text-[#C5A059]" />
                      <span>{session.start_time} - {session.end_time}</span>
                      <span>•</span>
                      <span>{session.duration_minutes}m</span>
                    </div>
                  </div>

                  {/* Quick toggle complete */}
                  <button
                    onClick={() =>
                      setSessionStatus(
                        session.id,
                        session.status === 'completed' ? 'upcoming' : 'completed'
                      )
                    }
                    className={`p-2 rounded-xl border transition-colors shrink-0 ${
                      isCompleted
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : 'bg-stone-50 text-stone-500 border-stone-200 hover:border-[#C5A059] hover:text-[#9A7426]'
                    }`}
                    title={isCompleted ? 'Mark as upcoming' : 'Mark as completed'}
                  >
                    <CheckCircle2 className="w-4 h-4" />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="mt-4 pt-3 border-t border-[#F4ECE1] text-[11px] text-stone-500 flex items-center justify-between">
        <span>Completed: {todaySessions.filter((s) => s.status === 'completed').length}/{todaySessions.length}</span>
        <span className="text-[#9A7426] font-medium">Daily Target: 4.5 hrs</span>
      </div>
    </Card>
  );
};
