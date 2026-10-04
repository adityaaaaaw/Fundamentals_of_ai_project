import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { Task, StudySession, Exam, DayStudyMetric, SessionStatus, TaskStatus } from '../types';
import { INITIAL_TASKS, INITIAL_SESSIONS, INITIAL_EXAMS, INITIAL_METRICS } from '../data/mockData';
import { taskService } from '../services/taskService';
import { sessionService } from '../services/sessionService';
import { examService } from '../services/examService';
import { dashboardService } from '../services/dashboardService';

interface ValidationResult {
  success: boolean;
  error?: string;
}

interface PlannerContextType {
  tasks: Task[];
  sessions: StudySession[];
  exams: Exam[];
  weeklyMetrics: DayStudyMetric[];
  isLoading: boolean;
  backendOnline: boolean;
  
  // Task Actions
  addTask: (task: Omit<Task, 'id' | 'created_at'>) => Promise<ValidationResult>;
  updateTask: (id: string, updates: Partial<Task>) => Promise<ValidationResult>;
  deleteTask: (id: string) => Promise<ValidationResult>;
  toggleTaskCompletion: (id: string) => Promise<void>;
  setTaskStatus: (id: string, status: TaskStatus) => Promise<void>;
  
  // Session Actions
  addSession: (session: Omit<StudySession, 'id'>) => Promise<ValidationResult>;
  updateSession: (id: string, updates: Partial<StudySession>) => Promise<ValidationResult>;
  deleteSession: (id: string) => Promise<ValidationResult>;
  setSessionStatus: (id: string, status: SessionStatus) => Promise<void>;
  
  // Exam Actions
  addExam: (exam: Omit<Exam, 'id'>) => Promise<ValidationResult>;
  deleteExam: (id: string) => Promise<ValidationResult>;
  
  // Stats
  totalTasks: number;
  completedTasks: number;
  pendingTasks: number;
  missedTasks: number;
  todaySessions: StudySession[];
  
  // Reset & Refresh
  resetToSampleData: () => void;
  refreshData: () => Promise<void>;
}

const PlannerContext = createContext<PlannerContextType | undefined>(undefined);

const LOCAL_STORAGE_KEYS = {
  TASKS: 'ai_planner_tasks_v1',
  SESSIONS: 'ai_planner_sessions_v1',
  EXAMS: 'ai_planner_exams_v1',
  MIGRATED_V2: 'ai_planner_migrated_v2',
};

export const PlannerProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [tasks, setTasks] = useState<Task[]>(INITIAL_TASKS);
  const [sessions, setSessions] = useState<StudySession[]>(INITIAL_SESSIONS);
  const [exams, setExams] = useState<Exam[]>(INITIAL_EXAMS);
  const [weeklyMetrics, setWeeklyMetrics] = useState<DayStudyMetric[]>(INITIAL_METRICS);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [backendOnline, setBackendOnline] = useState<boolean>(false);

  // Fetch all data from backend
  const refreshData = useCallback(async () => {
    try {
      const [backendTasks, backendSessions, backendExams, backendProgress] = await Promise.all([
        taskService.getTasks(),
        sessionService.getSessions(),
        examService.getExams(),
        dashboardService.getWeeklyProgress().catch(() => null),
      ]);

      setTasks(backendTasks || []);
      setSessions(backendSessions || []);
      setExams(backendExams || []);
      if (backendProgress && backendProgress.metrics && backendProgress.metrics.length > 0) {
        setWeeklyMetrics(backendProgress.metrics);
      }
      setBackendOnline(true);
    } catch (err) {
      console.warn('Backend not reachable or error during load; using local fallback:', err);
      setBackendOnline(false);
      try {
        const localTasks = localStorage.getItem(LOCAL_STORAGE_KEYS.TASKS);
        const localSessions = localStorage.getItem(LOCAL_STORAGE_KEYS.SESSIONS);
        const localExams = localStorage.getItem(LOCAL_STORAGE_KEYS.EXAMS);
        if (localTasks) setTasks(JSON.parse(localTasks));
        if (localSessions) setSessions(JSON.parse(localSessions));
        if (localExams) setExams(JSON.parse(localExams));
      } catch {
        // default to empty
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  // Task actions
  const addTask = async (taskData: Omit<Task, 'id' | 'created_at'>): Promise<ValidationResult> => {
    try {
      const created = await taskService.createTask(taskData);
      setTasks((prev) => [created, ...prev]);
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || 'Failed to create task.' };
    }
  };

  const updateTask = async (id: string, updates: Partial<Task>): Promise<ValidationResult> => {
    try {
      const updated = await taskService.updateTask(id, updates);
      setTasks((prev) => prev.map((t) => (t.id === id ? updated : t)));
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || 'Failed to update task.' };
    }
  };

  const deleteTask = async (id: string): Promise<ValidationResult> => {
    try {
      await taskService.deleteTask(id);
      setTasks((prev) => prev.filter((t) => t.id !== id));
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || 'Failed to delete task.' };
    }
  };

  const toggleTaskCompletion = async (id: string): Promise<void> => {
    const current = tasks.find((t) => t.id === id);
    if (!current) return;
    const nextStatus: TaskStatus = current.status === 'completed' ? 'pending' : 'completed';

    // Optimistic UI update
    setTasks((prev) => prev.map((t) => (t.id === id ? { ...t, status: nextStatus } : t)));
    try {
      await taskService.updateTaskStatus(id, nextStatus);
    } catch (err) {
      console.error('Failed to toggle task status:', err);
      // Rollback
      setTasks((prev) => prev.map((t) => (t.id === id ? current : t)));
    }
  };

  const setTaskStatus = async (id: string, status: TaskStatus): Promise<void> => {
    const current = tasks.find((t) => t.id === id);
    if (!current) return;

    setTasks((prev) => prev.map((t) => (t.id === id ? { ...t, status } : t)));
    try {
      await taskService.updateTaskStatus(id, status);
    } catch (err) {
      console.error('Failed to update task status:', err);
      setTasks((prev) => prev.map((t) => (t.id === id ? current : t)));
    }
  };

  // Session actions with conflict & overlap detection
  const addSession = async (sessionData: Omit<StudySession, 'id'>): Promise<ValidationResult> => {
    try {
      const created = await sessionService.createSession(sessionData);
      setSessions((prev) => [...prev, created]);
      // Refresh weekly metrics after adding a session
      dashboardService.getWeeklyProgress().then((res) => {
        if (res?.metrics) setWeeklyMetrics(res.metrics);
      }).catch(() => {});
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || 'Failed to schedule session.' };
    }
  };

  const updateSession = async (id: string, updates: Partial<StudySession>): Promise<ValidationResult> => {
    try {
      const updated = await sessionService.updateSession(id, updates);
      setSessions((prev) => prev.map((s) => (s.id === id ? updated : s)));
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || 'Failed to update session.' };
    }
  };

  const deleteSession = async (id: string): Promise<ValidationResult> => {
    try {
      await sessionService.deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || 'Failed to delete session.' };
    }
  };

  const setSessionStatus = async (id: string, status: SessionStatus): Promise<void> => {
    const current = sessions.find((s) => s.id === id);
    if (!current) return;

    setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, status } : s)));
    try {
      await sessionService.updateSessionStatus(id, status);
      dashboardService.getWeeklyProgress().then((res) => {
        if (res?.metrics) setWeeklyMetrics(res.metrics);
      }).catch(() => {});
    } catch (err) {
      console.error('Failed to update session status:', err);
      setSessions((prev) => prev.map((s) => (s.id === id ? current : s)));
    }
  };

  // Exam actions
  const addExam = async (examData: Omit<Exam, 'id'>): Promise<ValidationResult> => {
    try {
      const created = await examService.createExam(examData);
      setExams((prev) => [...prev, created]);
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || 'Failed to add exam.' };
    }
  };

  const deleteExam = async (id: string): Promise<ValidationResult> => {
    try {
      await examService.deleteExam(id);
      setExams((prev) => prev.filter((e) => e.id !== id));
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || 'Failed to delete exam.' };
    }
  };

  const resetToSampleData = () => {
    refreshData();
  };

  // Derived metrics
  const totalTasks = tasks.length;
  const completedTasks = tasks.filter((t) => t.status === 'completed').length;
  const pendingTasks = tasks.filter((t) => t.status === 'pending').length;
  const missedTasks = tasks.filter((t) => t.status === 'missed').length;

  const todayStr = new Date().toISOString().split('T')[0];
  const todayWeekday = new Date().toLocaleDateString('en-US', { weekday: 'long' });
  const todaySessions = sessions.filter(
    (s) => s.date === todayStr || s.day_of_week === todayWeekday || s.day_of_week === 'Monday'
  );

  return (
    <PlannerContext.Provider
      value={{
        tasks,
        sessions,
        exams,
        weeklyMetrics,
        isLoading,
        backendOnline,
        addTask,
        updateTask,
        deleteTask,
        toggleTaskCompletion,
        setTaskStatus,
        addSession,
        updateSession,
        deleteSession,
        setSessionStatus,
        addExam,
        deleteExam,
        totalTasks,
        completedTasks,
        pendingTasks,
        missedTasks,
        todaySessions,
        resetToSampleData,
        refreshData,
      }}
    >
      {children}
    </PlannerContext.Provider>
  );
};

export const usePlanner = () => {
  const context = useContext(PlannerContext);
  if (!context) {
    throw new Error('usePlanner must be used within a PlannerProvider');
  }
  return context;
};
