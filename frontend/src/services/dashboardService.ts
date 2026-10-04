import apiClient from './api';
import type { Task, StudySession, Exam, DayStudyMetric } from '../types';

export interface DashboardSummaryData {
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  missed_tasks: number;
  in_progress_tasks: number;
  completion_rate: number;
  planned_study_time_minutes: number;
  completed_study_time_minutes: number;
  current_streak_days: number;
}

export interface WeeklyProgressData {
  metrics: DayStudyMetric[];
  total_studied_hours: number;
  total_target_hours: number;
  current_streak_days: number;
}

export const dashboardService = {
  async getSummary(): Promise<DashboardSummaryData> {
    const res = await apiClient.get<DashboardSummaryData>('/dashboard/summary');
    return res.data;
  },

  async getWeeklyProgress(): Promise<WeeklyProgressData> {
    const res = await apiClient.get<WeeklyProgressData>('/dashboard/weekly-progress');
    return res.data;
  },

  async getTodaySessions(): Promise<StudySession[]> {
    const res = await apiClient.get<StudySession[]>('/dashboard/today-sessions');
    return res.data;
  },

  async getUpcomingExams(): Promise<Exam[]> {
    const res = await apiClient.get<Exam[]>('/dashboard/upcoming-exams');
    return res.data;
  },

  async getHighPriorityTasks(): Promise<Task[]> {
    const res = await apiClient.get<Task[]>('/dashboard/high-priority-tasks');
    return res.data;
  },
};
