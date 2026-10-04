import React from 'react';
import { Award, Calendar, MapPin, AlertTriangle } from 'lucide-react';
import { Card } from '../common/Card';
import { usePlanner } from '../../context/PlannerContext';

export const UpcomingExams: React.FC = () => {
  const { exams } = usePlanner();

  const getDaysRemaining = (examDateStr: string) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const examDate = new Date(examDateStr);
    examDate.setHours(0, 0, 0, 0);

    const diffTime = examDate.getTime() - today.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  return (
    <Card className="flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#F4ECE1]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#FAF4E6] flex items-center justify-center text-[#B08B44]">
              <Award className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-heading font-bold text-base text-stone-900">
                Upcoming Exams
              </h3>
              <p className="text-xs text-stone-500">
                Important milestones & revision targets
              </p>
            </div>
          </div>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-[#FAF3E0] text-[#9A7326] border border-[#ECD9AF]">
            {exams.length} upcoming
          </span>
        </div>

        {exams.length === 0 ? (
          <div className="py-8 text-center">
            <div className="w-12 h-12 rounded-full bg-stone-100 flex items-center justify-center mx-auto mb-2 text-stone-400">
              <Award className="w-6 h-6" />
            </div>
            <p className="text-xs font-medium text-stone-600">
              No upcoming exams.
            </p>
            <p className="text-[11px] text-stone-400 mt-0.5">
              Add your upcoming exams and milestones to track countdowns.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {exams.map((exam) => {
              const daysLeft = getDaysRemaining(exam.date);
              const isUrgent = daysLeft <= 7;

              return (
                <div
                  key={exam.id}
                  className="p-3.5 rounded-xl border border-[#EFEAE1] hover:border-[#DFC790] bg-white transition-all duration-150 shadow-2xs"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[11px] font-bold text-[#8B6E30] bg-[#FAF4E6] px-2 py-0.5 rounded-md border border-[#ECDDBF]">
                          {exam.subject}
                        </span>
                        {exam.weight && (
                          <span className="text-[10px] font-semibold text-stone-500">
                            {exam.weight}
                          </span>
                        )}
                      </div>
                      <h4 className="text-sm font-semibold text-stone-900">
                        {exam.title}
                      </h4>
                    </div>

                    <span
                      className={`shrink-0 text-xs font-semibold px-2.5 py-1 rounded-full border flex items-center gap-1 ${
                        isUrgent
                          ? 'bg-rose-50 text-rose-700 border-rose-200'
                          : 'bg-[#FAF3E0] text-[#9A7326] border-[#E8D9B5]'
                      }`}
                    >
                      {isUrgent && <AlertTriangle className="w-3 h-3 text-rose-600" />}
                      <span>{daysLeft <= 0 ? 'Today' : `In ${daysLeft} days`}</span>
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2.5 text-xs text-stone-500">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-stone-400" />
                      <span>{exam.date} • {exam.time}</span>
                    </div>

                    {exam.room && (
                      <div className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-stone-400" />
                        <span>{exam.room}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="mt-4 pt-3 border-t border-[#F4ECE1] text-[11px] text-stone-500 flex items-center justify-between">
        <span>Plan revision sessions in Schedule</span>
        <span className="text-[#9A7426] font-semibold">Priority Focus</span>
      </div>
    </Card>
  );
};
