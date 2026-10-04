import apiClient from './api';
import type { Task, TaskStatus, Priority } from '../types';

export interface TaskQueryParams {
  status?: TaskStatus | 'all';
  priority?: Priority | 'all';
  subject?: string;
  due_date?: string;
  search?: string;
  skip?: number;
  limit?: number;
}

export const taskService = {
  async getTasks(params?: TaskQueryParams): Promise<Task[]> {
    const res = await apiClient.get<Task[]>('/tasks', { params });
    return res.data;
  },

  async getTask(id: string): Promise<Task> {
    const res = await apiClient.get<Task>(`/tasks/${id}`);
    return res.data;
  },

  async createTask(taskData: Omit<Task, 'id' | 'created_at'>): Promise<Task> {
    const res = await apiClient.post<Task>('/tasks', taskData);
    return res.data;
  },

  async updateTask(id: string, updates: Partial<Task>): Promise<Task> {
    const res = await apiClient.put<Task>(`/tasks/${id}`, updates);
    return res.data;
  },

  async updateTaskStatus(id: string, status: TaskStatus): Promise<Task> {
    const res = await apiClient.patch<Task>(`/tasks/${id}/status`, { status });
    return res.data;
  },

  async deleteTask(id: string): Promise<void> {
    await apiClient.delete(`/tasks/${id}`);
  },
};
