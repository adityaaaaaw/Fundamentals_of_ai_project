import apiClient from './api';
import type { Exam } from '../types';

export const examService = {
  async getExams(): Promise<Exam[]> {
    const res = await apiClient.get<Exam[]>('/exams');
    return res.data;
  },

  async getExam(id: string): Promise<Exam> {
    const res = await apiClient.get<Exam>(`/exams/${id}`);
    return res.data;
  },

  async createExam(examData: Omit<Exam, 'id'>): Promise<Exam> {
    const res = await apiClient.post<Exam>('/exams', examData);
    return res.data;
  },

  async updateExam(id: string, updates: Partial<Exam>): Promise<Exam> {
    const res = await apiClient.put<Exam>(`/exams/${id}`, updates);
    return res.data;
  },

  async deleteExam(id: string): Promise<void> {
    await apiClient.delete(`/exams/${id}`);
  },
};
