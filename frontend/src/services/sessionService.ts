import apiClient from './api';
import type { StudySession, SessionStatus, DayOfWeek } from '../types';

export interface SessionQueryParams {
  date?: string;
  day_of_week?: DayOfWeek | 'All';
  status?: SessionStatus | 'all';
}

export const sessionService = {
  async getSessions(params?: SessionQueryParams): Promise<StudySession[]> {
    const res = await apiClient.get<StudySession[]>('/sessions', { params });
    return res.data;
  },

  async getSession(id: string): Promise<StudySession> {
    const res = await apiClient.get<StudySession>(`/sessions/${id}`);
    return res.data;
  },

  async createSession(sessionData: Omit<StudySession, 'id'>): Promise<StudySession> {
    const res = await apiClient.post<StudySession>('/sessions', sessionData);
    return res.data;
  },

  async updateSession(id: string, updates: Partial<StudySession>): Promise<StudySession> {
    const res = await apiClient.put<StudySession>(`/sessions/${id}`, updates);
    return res.data;
  },

  async updateSessionStatus(id: string, status: SessionStatus): Promise<StudySession> {
    const res = await apiClient.patch<StudySession>(`/sessions/${id}/status`, { status });
    return res.data;
  },

  async deleteSession(id: string): Promise<void> {
    await apiClient.delete(`/sessions/${id}`);
  },
};
