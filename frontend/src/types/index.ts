export type Priority = 'low' | 'medium' | 'high';
export type TaskStatus = 'pending' | 'completed' | 'missed';
export type SessionStatus = 'upcoming' | 'completed' | 'missed';

export interface Task {
  id: string;
  title: string;
  subject: string;
  due_date: string; // YYYY-MM-DD
  priority: Priority;
  status: TaskStatus;
  notes?: string;
  created_at?: string;
}

export type DayOfWeek = 
  | 'Monday' 
  | 'Tuesday' 
  | 'Wednesday' 
  | 'Thursday' 
  | 'Friday' 
  | 'Saturday' 
  | 'Sunday';

export interface StudySession {
  id: string;
  subject: string;
  date: string; // YYYY-MM-DD
  day_of_week: DayOfWeek;
  start_time: string; // HH:MM (24-hour)
  end_time: string;   // HH:MM (24-hour)
  duration_minutes: number;
  topic: string;
  status: SessionStatus;
  color?: string;
}

export interface Exam {
  id: string;
  subject: string;
  title: string;
  date: string; // YYYY-MM-DD
  time: string;
  room?: string;
  weight?: string;
  days_remaining?: number;
}

export interface DayStudyMetric {
  day: string; // 'Mon', 'Tue', etc.
  fullDay: DayOfWeek;
  studiedHours: number;
  targetHours: number;
}
