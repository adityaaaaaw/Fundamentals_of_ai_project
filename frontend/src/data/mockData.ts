import type { Task, StudySession, Exam, DayStudyMetric } from '../types';

// Clean initial empty datasets (no demo data)
export const INITIAL_TASKS: Task[] = [];

export const INITIAL_SESSIONS: StudySession[] = [];

export const INITIAL_EXAMS: Exam[] = [];

export const INITIAL_METRICS: DayStudyMetric[] = [
  { day: 'Mon', fullDay: 'Monday', studiedHours: 0.0, targetHours: 4.0 },
  { day: 'Tue', fullDay: 'Tuesday', studiedHours: 0.0, targetHours: 3.5 },
  { day: 'Wed', fullDay: 'Wednesday', studiedHours: 0.0, targetHours: 4.0 },
  { day: 'Thu', fullDay: 'Thursday', studiedHours: 0.0, targetHours: 3.5 },
  { day: 'Fri', fullDay: 'Friday', studiedHours: 0.0, targetHours: 4.0 },
  { day: 'Sat', fullDay: 'Saturday', studiedHours: 0.0, targetHours: 4.5 },
  { day: 'Sun', fullDay: 'Sunday', studiedHours: 0.0, targetHours: 3.0 },
];
