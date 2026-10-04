import React, { useState } from 'react';
import { Plus, Search, CheckCircle2, Clock, XCircle, ListTodo } from 'lucide-react';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { TaskItem } from '../components/tasks/TaskItem';
import { TaskModal } from '../components/tasks/TaskModal';
import { usePlanner } from '../context/PlannerContext';
import type { Task, TaskStatus } from '../types';

export const Tasks: React.FC = () => {
  const { tasks, totalTasks, completedTasks, pendingTasks, missedTasks } = usePlanner();

  const [activeTab, setActiveTab] = useState<'all' | TaskStatus>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [subjectFilter, setSubjectFilter] = useState<string>('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [taskToEdit, setTaskToEdit] = useState<Task | null>(null);

  // Extract unique subjects
  const subjects = Array.from(new Set(tasks.map((t) => t.subject))).filter(Boolean);

  // Filter tasks
  const filteredTasks = tasks.filter((t) => {
    const matchesTab = activeTab === 'all' || t.status === activeTab;
    const matchesSubject = subjectFilter === 'all' || t.subject === subjectFilter;
    const matchesSearch =
      t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (t.notes && t.notes.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesTab && matchesSubject && matchesSearch;
  });

  const handleEdit = (task: Task) => {
    setTaskToEdit(task);
    setIsModalOpen(true);
  };

  const handleCreateNew = () => {
    setTaskToEdit(null);
    setIsModalOpen(true);
  };

  const tabs = [
    { id: 'all' as const, label: 'All Tasks', count: totalTasks, icon: ListTodo },
    { id: 'pending' as const, label: 'Pending', count: pendingTasks, icon: Clock },
    { id: 'completed' as const, label: 'Completed', count: completedTasks, icon: CheckCircle2 },
    { id: 'missed' as const, label: 'Missed', count: missedTasks, icon: XCircle },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#EFEAE1]">
        <div>
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-stone-900 tracking-tight">
            My Coursework Tasks
          </h2>
          <p className="text-xs sm:text-sm text-stone-500 mt-1">
            Track homework, assignments, and exam prep with deadlines & priorities
          </p>
        </div>

        <Button
          variant="primary"
          onClick={handleCreateNew}
          icon={<Plus className="w-4 h-4" />}
          className="shadow-soft self-start sm:self-auto"
        >
          Add Task
        </Button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isSelected = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-150 border ${
                isSelected
                  ? 'bg-white text-stone-900 border-[#C5A059] shadow-soft ring-1 ring-[#C5A059]/20'
                  : 'bg-white/60 text-stone-500 border-[#EFEAE1] hover:bg-white hover:text-stone-800'
              }`}
            >
              <Icon className={`w-4 h-4 ${isSelected ? 'text-[#B08B44]' : 'text-stone-400'}`} />
              <span>{tab.label}</span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                  isSelected
                    ? 'bg-[#FAF3E0] text-[#9A7326] border border-[#E8D9B5]'
                    : 'bg-stone-100 text-stone-500'
                }`}
              >
                {tab.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Search & Subject filter bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3 bg-white p-3 sm:p-4 rounded-2xl border border-[#EFEAE1] shadow-2xs">
        {/* Search Input */}
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-stone-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by task title, topic, or subject..."
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-stone-200 bg-stone-50/50 text-xs sm:text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white transition-all"
          />
        </div>

        {/* Subject Dropdown */}
        <div className="w-full sm:w-56 shrink-0">
          <select
            value={subjectFilter}
            onChange={(e) => setSubjectFilter(e.target.value)}
            className="w-full px-3 py-2 rounded-xl border border-stone-200 bg-stone-50/50 text-xs sm:text-sm text-stone-900 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white"
          >
            <option value="all">All Subjects</option>
            {subjects.map((sub) => (
              <option key={sub} value={sub}>
                {sub}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Task List */}
      {filteredTasks.length === 0 ? (
        <Card className="py-14 text-center">
          <div className="w-14 h-14 rounded-2xl bg-[#FAF6F0] border border-[#ECD9AF] text-[#C5A059] flex items-center justify-center mx-auto mb-3">
            <ListTodo className="w-7 h-7 text-[#B08B44]" />
          </div>
          <h3 className="font-heading font-bold text-base text-stone-900">
            {tasks.length === 0 ? 'No tasks yet. Add your first task to get started.' : 'No Tasks Found'}
          </h3>
          <p className="text-xs text-stone-500 mt-1 max-w-sm mx-auto">
            {tasks.length === 0
              ? 'Organize your assignments and exam prep by adding coursework tasks.'
              : searchQuery
              ? `No tasks match your search "${searchQuery}".`
              : 'There are no tasks matching your selected filters.'}
          </p>
          <div className="mt-4">
            <Button
              variant="primary"
              size="sm"
              onClick={handleCreateNew}
              icon={<Plus className="w-4 h-4" />}
            >
              Create New Task
            </Button>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredTasks.map((task) => (
            <TaskItem
              key={task.id}
              task={task}
              onEdit={handleEdit}
            />
          ))}
        </div>
      )}

      {/* Task Modal */}
      <TaskModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setTaskToEdit(null);
        }}
        taskToEdit={taskToEdit}
      />
    </div>
  );
};
