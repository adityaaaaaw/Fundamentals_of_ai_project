import { apiClient, aiApiClient } from './api';

export interface StudyBlock {
  time: string;
  start_time?: string;
  end_time?: string;
  subject: string;
  topic: string;
  duration_minutes: number;
  strategy: string;
  break_recommendation?: string;
  priority?: string;
}

export interface GeneratePlanRequest {
  goal: string;
  subject?: string;
  available_hours?: number;
  target_date?: string;
  preferred_duration?: number;
  instructions?: string;
}

export interface GeneratePlanResponse {
  goal: string;
  summary: string;
  total_hours: number;
  blocks: StudyBlock[];
}

export interface AskRequest {
  question: string;
  context?: string;
}

export interface AskResponse {
  answer: string;
  suggested_actions: string[];
}

export interface OptimizeScheduleRequest {
  target_date?: string;
  available_hours?: number;
  preferences?: string;
}

export interface OptimizeScheduleResponse {
  summary: string;
  recommendations: StudyBlock[];
}

// Phase 3 & Phase 5 Agent Enhancements Types
export type EventType = 'study' | 'exam' | 'meal' | 'sleep' | 'fixed';

export type AgentStepStatus =
  | 'processing'
  | 'retrieving_data'
  | 'executing_action'
  | 'awaiting_approval'
  | 'completed'
  | 'failed';

export interface AgentWorkflowStep {
  step_id: number;
  name: string;
  status: AgentStepStatus;
  summary: string;
}

export interface ProposedSessionBlock {
  subject: string;
  topic: string;
  date: string; // YYYY-MM-DD
  start_time: string; // HH:MM
  end_time: string; // HH:MM
  duration_minutes: number;
  reason: string;
  event_type?: EventType;
  status?: string;
  color?: string;
}

export interface AgentExecuteRequest {
  prompt: string;
  preferred_hours?: number;
  target_date?: string;
  timezone?: string;
}

export interface AgentExecuteResponse {
  prompt: string;
  action_type: string;
  tool_name: string;
  summary: string;
  explanation: string;
  steps: AgentWorkflowStep[];
  requires_approval: boolean;
  proposed_sessions: ProposedSessionBlock[];
  target_date?: string;
  timezone?: string;
  assumptions?: string[];
  is_general_recommendation?: boolean;
  constraint_errors?: string[];
  data_snapshot?: Record<string, any>;
}

export interface ScheduleApprovalRequest {
  sessions: ProposedSessionBlock[];
  log_id?: string;
}

export interface ScheduleApprovalResponse {
  approved: boolean;
  saved_count: number;
  rejected_count: number;
  message: string;
  saved_session_ids: string[];
}

export interface ScheduleRejectRequest {
  reason?: string;
  log_id?: string;
}

export interface ScheduleRejectResponse {
  approved: boolean;
  message: string;
}

export interface AgentActivityLogResponse {
  id: string;
  action_type: string;
  tool_name: string;
  summary: string;
  status: string;
  created_at?: string;
}

export const aiService = {
  async generatePlan(request: GeneratePlanRequest): Promise<GeneratePlanResponse> {
    const res = await aiApiClient.post<GeneratePlanResponse>('/ai/generate-plan', request);
    return res.data;
  },

  async askAssistant(request: AskRequest): Promise<AskResponse> {
    const res = await aiApiClient.post<AskResponse>('/ai/ask', request);
    return res.data;
  },

  async optimizeSchedule(request: OptimizeScheduleRequest): Promise<OptimizeScheduleResponse> {
    const res = await aiApiClient.post<OptimizeScheduleResponse>('/ai/optimize-schedule', request);
    return res.data;
  },

  // Phase 3 & 5 Agent Services with Timezone Detection
  async executeAgentWorkflow(request: AgentExecuteRequest): Promise<AgentExecuteResponse> {
    const userTimezone = request.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
    const payload: AgentExecuteRequest = {
      ...request,
      timezone: userTimezone,
    };
    const res = await aiApiClient.post<AgentExecuteResponse>('/ai/agent/execute', payload);
    return res.data;
  },

  async approveSchedule(request: ScheduleApprovalRequest): Promise<ScheduleApprovalResponse> {
    const res = await apiClient.post<ScheduleApprovalResponse>('/ai/schedule/approve', request);
    return res.data;
  },

  async rejectSchedule(request: ScheduleRejectRequest): Promise<ScheduleRejectResponse> {
    const res = await apiClient.post<ScheduleRejectResponse>('/ai/schedule/reject', request);
    return res.data;
  },

  async getLogs(): Promise<AgentActivityLogResponse[]> {
    const res = await apiClient.get<AgentActivityLogResponse[]>('/ai/logs');
    return res.data;
  },
};

