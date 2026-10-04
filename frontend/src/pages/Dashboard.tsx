import React from 'react';
import { Link } from 'react-router-dom';
import { Header } from '../components/layout/Header';
import { StatCards } from '../components/dashboard/StatCards';
import { TodaySessions } from '../components/dashboard/TodaySessions';
import { ProgressChart } from '../components/dashboard/ProgressChart';
import { UpcomingExams } from '../components/dashboard/UpcomingExams';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { usePlanner } from '../context/PlannerContext';
import { CheckSquare, ArrowRight, Sparkles } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { tasks, toggleTaskCompletion } = usePlanner();

  const pendingTasksList = tasks.filter((t) => t.status === 'pending').slice(0, 4);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <Header
        title="Welcome to your Study Planner 🎓"
        subtitle="Stay focused, review your goals, and master your subjects."
      />

      {/* AI Assistant Callout Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-[#FAF3E0] via-[#FDFBF7] to-[#FAF3E0] border border-[#ECD9AF] p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-soft">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-white border border-[#E8D9B5] text-[#C5A059] flex items-center justify-center shrink-0 shadow-xs">
            <Sparkles className="w-5 h-5 text-[#B08B44]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-heading font-bold text-sm sm:text-base text-stone-900">
                Autonomous AI Study Planner Agent
              </h3>
              <span className="px-2 py-0.5 text-[10px] font-bold tracking-wide uppercase rounded-md bg-[#C5A059] text-white">
                Live Agent
              </span>
            </div>
            <p className="text-xs text-stone-600 mt-1 max-w-xl leading-relaxed">
              Generate personalized revision plans, optimize study schedules, and catch up on missed sessions with Gemini function calling and human-in-the-loop approvals.
            </p>
          </div>
        </div>

        <Link
          to="/assistant"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-[#C5A059] text-white hover:bg-[#B38E46] transition-colors shrink-0 shadow-xs justify-center"
        >
          <span>Explore Assistant</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Summary Stat Cards */}
      <StatCards />

      {/* Primary Dashboard Grid: Today's Sessions & Weekly Progress */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TodaySessions />
        <ProgressChart />
      </div>

      {/* Secondary Grid: Upcoming Exams & Urgent Tasks */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <UpcomingExams />

        {/* Priority Pending Tasks Card */}
        <Card className="flex flex-col justify-between h-full">
          <div>
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#F4ECE1]">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-[#FAF4E6] flex items-center justify-center text-[#B08B44]">
                  <CheckSquare className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-heading font-bold text-base text-stone-900">
                    High Priority Tasks
                  </h3>
                  <p className="text-xs text-stone-500">
                    Next coursework items to tackle
                  </p>
                </div>
              </div>

              <Link
                to="/tasks"
                className="inline-flex items-center gap-1 text-xs font-semibold text-[#9A7426] hover:text-[#7A5918] transition-colors"
              >
                <span>View All Tasks</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {pendingTasksList.length === 0 ? (
              <div className="py-8 text-center">
                <p className="text-xs font-medium text-stone-500">
                  No tasks yet. Add your first task to get started.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {pendingTasksList.map((task) => (
                  <div
                    key={task.id}
                    className="p-3.5 rounded-xl border border-[#EFEAE1] hover:border-[#DFC790] bg-white transition-all flex items-start justify-between gap-3"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[11px] font-semibold text-[#8B6E30] bg-[#FAF4E6] px-2 py-0.5 rounded-md border border-[#ECDDBF]">
                          {task.subject}
                        </span>
                        <Badge variant="priority" value={task.priority} size="sm" />
                      </div>
                      <h4 className="text-xs sm:text-sm font-semibold text-stone-900 leading-snug truncate">
                        {task.title}
                      </h4>
                      <p className="text-[11px] text-stone-500 mt-1">
                        Due: {task.due_date}
                      </p>
                    </div>

                    <button
                      onClick={() => toggleTaskCompletion(task.id)}
                      className="text-xs px-2.5 py-1.5 rounded-lg border border-stone-200 text-stone-600 hover:border-emerald-500 hover:text-emerald-700 hover:bg-emerald-50 transition-colors shrink-0 font-medium"
                    >
                      Done
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-[#F4ECE1] text-[11px] text-stone-500 flex items-center justify-between">
            <span>Keep your momentum going!</span>
            <span className="text-[#9A7426] font-semibold">{pendingTasksList.length} items shown</span>
          </div>
        </Card>
      </div>
    </div>
  );
};
