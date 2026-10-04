import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Send,
  CalendarPlus,
  Check,
  ArrowRight,
  Lightbulb,
  Clock,
  BookOpen,
  AlertCircle,
  Loader2,
  HelpCircle,
  CalendarCheck,
  CheckCircle2,
  XCircle,
  Bot,
  Workflow,
  ShieldCheck,
  History,
  RefreshCw,
  Calendar,
  Globe,
  Moon,
  Utensils,
  Info,
  Briefcase,
} from 'lucide-react';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { usePlanner } from '../context/PlannerContext';
import {
  aiService,
  type StudyBlock,
  type GeneratePlanResponse,
  type AskResponse,
  type AgentExecuteResponse,
  type AgentActivityLogResponse,
  type AgentWorkflowStep,
  type EventType,
} from '../services/aiService';


const SAMPLE_AGENT_PROMPTS = [
  {
    category: 'Progress',
    prompt: 'How am I progressing with my tasks and exams?',
    badge: 'Data Retrieval',
  },
  {
    category: 'Rescheduling',
    prompt: 'Reschedule my missed study sessions to available slots this week',
    badge: 'Safe Tool Execution',
  },
  {
    category: 'Study Plan',
    prompt: 'Generate a structured revision plan for my upcoming coursework',
    badge: 'Constraint Validation',
  },
  {
    category: 'Optimization',
    prompt: 'Optimize my study schedule to avoid burnout and balance workloads',
    badge: 'Schedule Balancing',
  },
  {
    category: 'Academic Coaching',
    prompt: 'What study methods are most effective for active recall?',
    badge: 'Cognitive Strategy',
  },
];

export const AIAssistant: React.FC = () => {
  const { addSession, refreshData, backendOnline } = usePlanner();

  const [activeTab, setActiveTab] = useState<'agent' | 'plan' | 'ask' | 'logs'>('agent');
  const [promptInput, setPromptInput] = useState('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [statusNotice, setStatusNotice] = useState<string | null>(null);

  // Agent State (Phase 3 & 4)
  const [agentResult, setAgentResult] = useState<AgentExecuteResponse | null>(null);
  const [activeAgentQuery, setActiveAgentQuery] = useState<string | null>(null);
  const [isApproving, setIsApproving] = useState<boolean>(false);
  const [isRejecting, setIsRejecting] = useState<boolean>(false);
  const [approvalDecision, setApprovalDecision] = useState<'approved' | 'rejected' | null>(null);

  // Agent Activity Logs State
  const [activityLogs, setActivityLogs] = useState<AgentActivityLogResponse[]>([]);
  const [isLoadingLogs, setIsLoadingLogs] = useState<boolean>(false);

  // Plan Generator State (Clean initial state - no mock data)
  const [planResponse, setPlanResponse] = useState<GeneratePlanResponse | null>(null);
  const [isRealAiOutput, setIsRealAiOutput] = useState<boolean>(false);
  const [addedBlocks, setAddedBlocks] = useState<Record<number, boolean>>({});

  // Ask Advisor State (Phase 2)
  const [askHistory, setAskHistory] = useState<Array<{ q: string; a: AskResponse }>>([]);

  const fetchLogs = async () => {
    setIsLoadingLogs(true);
    try {
      const logs = await aiService.getLogs();
      setActivityLogs(logs);
    } catch {
      // ignore silently if backend offline
    } finally {
      setIsLoadingLogs(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'logs') {
      fetchLogs();
    }
  }, [activeTab]);

  const handleExecuteAgent = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = promptInput.trim();
    if (!query || isProcessing) return;

    setActiveAgentQuery(query);
    setPromptInput('');
    setErrorMessage(null);
    setStatusNotice(null);
    setApprovalDecision(null);
    setIsProcessing(true);

    try {
      const response = await aiService.executeAgentWorkflow({ prompt: query });
      setAgentResult(response);
    } catch (err: any) {
      setPromptInput(query);
      setErrorMessage(
        err.message || 'AI Agent failed to execute workflow. Verify backend service is running.'
      );
    } finally {
      setIsProcessing(false);
    }
  };

  const handleApproveProposal = async () => {
    if (!agentResult || agentResult.proposed_sessions.length === 0 || isApproving) return;

    setIsApproving(true);
    setErrorMessage(null);
    try {
      const res = await aiService.approveSchedule({
        sessions: agentResult.proposed_sessions,
      });

      if (res.approved) {
        setApprovalDecision('approved');
        setStatusNotice(res.message);
        await refreshData();
      } else {
        setErrorMessage(res.message);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to persist approved sessions.');
    } finally {
      setIsApproving(false);
    }
  };

  const handleRejectProposal = async () => {
    if (!agentResult || isRejecting) return;

    setIsRejecting(true);
    setErrorMessage(null);
    try {
      const res = await aiService.rejectSchedule({
        reason: 'Student rejected proposed schedule modifications.',
      });
      setApprovalDecision('rejected');
      setStatusNotice(res.message);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error recording rejection.');
    } finally {
      setIsRejecting(false);
    }
  };

  const handleSendPromptDirect = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = promptInput.trim();
    if (!query || isProcessing) return;

    setPromptInput('');
    setErrorMessage(null);
    setStatusNotice(null);
    setIsProcessing(true);

    if (activeTab === 'plan') {
      try {
        const response = await aiService.generatePlan({ goal: query });
        setPlanResponse(response);
        setIsRealAiOutput(true);
        setAddedBlocks({});
      } catch (err: any) {
        setPromptInput(query);
        setErrorMessage(
          err.message || 'AI service unavailable. Please check that GEMINI_API_KEY is configured in backend/.env'
        );
      } finally {
        setIsProcessing(false);
      }
    } else if (activeTab === 'ask') {
      try {
        const response = await aiService.askAssistant({ question: query });
        setAskHistory((prev) => [{ q: query, a: response }, ...prev]);
      } catch (err: any) {
        setPromptInput(query);
        setErrorMessage(
          err.message || 'AI advisor unavailable. Please check that GEMINI_API_KEY is configured in backend/.env'
        );
      } finally {
        setIsProcessing(false);
      }
    }
  };

  const handleImportBlock = async (block: StudyBlock, index: number) => {
    const todayStr = new Date().toISOString().split('T')[0];

    let start = block.start_time;
    let end = block.end_time;
    if (!start || !end) {
      const parts = block.time.split(' - ');
      start = parts[0]?.trim() || '10:00';
      end = parts[1]?.trim() || '11:00';
    }

    const result = await addSession({
      subject: block.subject,
      topic: block.topic,
      date: todayStr,
      day_of_week: 'Monday',
      start_time: start,
      end_time: end,
      duration_minutes: block.duration_minutes || 60,
      status: 'upcoming',
      color: '#C5A059',
    });

    if (result.success) {
      setAddedBlocks((prev) => ({ ...prev, [index]: true }));
      setStatusNotice(`Added "${block.topic}" to your Study Schedule!`);
      setTimeout(() => setStatusNotice(null), 4000);
    } else {
      setErrorMessage(result.error || 'Conflict detected: this time overlaps with an existing session.');
      setTimeout(() => setErrorMessage(null), 6000);
    }
  };

  const handleImportAll = async () => {
    if (!planResponse || !planResponse.blocks) return;
    const todayStr = new Date().toISOString().split('T')[0];
    let successCount = 0;
    let conflictCount = 0;

    for (let idx = 0; idx < planResponse.blocks.length; idx++) {
      if (addedBlocks[idx]) continue;

      const block = planResponse.blocks[idx];
      let start = block.start_time;
      let end = block.end_time;
      if (!start || !end) {
        const parts = block.time.split(' - ');
        start = parts[0]?.trim() || '10:00';
        end = parts[1]?.trim() || '11:00';
      }

      const res = await addSession({
        subject: block.subject,
        topic: block.topic,
        date: todayStr,
        day_of_week: 'Monday',
        start_time: start,
        end_time: end,
        duration_minutes: block.duration_minutes || 60,
        status: 'upcoming',
      });

      if (res.success) {
        successCount++;
        setAddedBlocks((prev) => ({ ...prev, [idx]: true }));
      } else {
        conflictCount++;
      }
    }

    if (successCount > 0) {
      const msg = `Successfully imported ${successCount} session(s) into your schedule!${
        conflictCount > 0 ? ` (${conflictCount} skipped due to time conflicts)` : ''
      }`;
      setStatusNotice(msg);
      setTimeout(() => setStatusNotice(null), 5000);
    } else if (conflictCount > 0) {
      setErrorMessage('Could not import sessions: all recommended times conflict with existing study sessions.');
      setTimeout(() => setErrorMessage(null), 6000);
    }
  };

  const renderStepStatusBadge = (status: AgentWorkflowStep['status']) => {
    switch (status) {
      case 'completed':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            Completed
          </span>
        );
      case 'processing':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded-md bg-sky-50 text-sky-700 border border-sky-200 flex items-center gap-1">
            <Loader2 className="w-3 h-3 text-sky-600 animate-spin" />
            Processing
          </span>
        );
      case 'retrieving_data':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded-md bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1">
            <Loader2 className="w-3 h-3 text-amber-600 animate-spin" />
            Retrieving data
          </span>
        );
      case 'executing_action':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded-md bg-purple-50 text-purple-700 border border-purple-200 flex items-center gap-1">
            <Loader2 className="w-3 h-3 text-purple-600 animate-spin" />
            Executing action
          </span>
        );
      case 'awaiting_approval':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded-md bg-amber-100 text-amber-900 border border-amber-300 flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-amber-700" />
            Awaiting approval
          </span>
        );
      case 'failed':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded-md bg-rose-50 text-rose-700 border border-rose-200 flex items-center gap-1">
            <XCircle className="w-3 h-3 text-rose-600" />
            Failed
          </span>
        );
      default:
        return null;
    }
  };

  const renderEventTypeBadge = (type?: EventType) => {
    switch (type) {
      case 'exam':
        return (
          <span className="text-[10px] font-bold uppercase tracking-wider text-rose-700 bg-rose-50 px-2 py-0.5 rounded-md border border-rose-200 flex items-center gap-1 shadow-2xs">
            <AlertCircle className="w-3 h-3 text-rose-600" />
            Scheduled Exam
          </span>
        );
      case 'sleep':
        return (
          <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-200 flex items-center gap-1 shadow-2xs">
            <Moon className="w-3 h-3 text-indigo-600" />
            Sleep Window
          </span>
        );
      case 'meal':
        return (
          <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200 flex items-center gap-1 shadow-2xs">
            <Utensils className="w-3 h-3 text-emerald-600" />
            Meal Break
          </span>
        );
      case 'fixed':
        return (
          <span className="text-[10px] font-bold uppercase tracking-wider text-purple-700 bg-purple-50 px-2 py-0.5 rounded-md border border-purple-200 flex items-center gap-1 shadow-2xs">
            <Briefcase className="w-3 h-3 text-purple-600" />
            Fixed Commitment
          </span>
        );
      case 'study':
      default:
        return (
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#8B6E30] bg-[#FAF4E6] px-2 py-0.5 rounded-md border border-[#ECDDBF] flex items-center gap-1 shadow-2xs">
            <BookOpen className="w-3 h-3 text-[#B08B44]" />
            Study Session
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#EFEAE1]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-7 h-7 rounded-lg bg-[#FAF3E0] border border-[#E8D9B5] flex items-center justify-center text-[#B08B44]">
              <Bot className="w-4 h-4" />
            </div>
            <span className="text-xs font-bold uppercase tracking-wider text-[#A07C2F]">
              AI Study Planner Agent
            </span>
            <span
              className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded-md border ${
                backendOnline
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-amber-50 text-amber-700 border-amber-200'
              }`}
            >
              {backendOnline ? 'API Connected' : 'Offline Mode'}
            </span>
          </div>

          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-stone-900 tracking-tight">
            Autonomous Academic Agent
          </h2>
          <p className="text-xs sm:text-sm text-stone-500 mt-1">
            Explicit tool-calling workflow with conflict validation, transparent reasoning, and safe approval.
          </p>
        </div>

        {/* Mode Switcher Tabs */}
        <div className="flex items-center gap-1 p-1 bg-white rounded-xl border border-[#EFEAE1] shadow-2xs self-start sm:self-auto overflow-x-auto max-w-full">
          <button
            onClick={() => setActiveTab('agent')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
              activeTab === 'agent'
                ? 'bg-[#C5A059] text-white shadow-xs'
                : 'text-stone-600 hover:text-stone-900 hover:bg-stone-50'
            }`}
          >
            <Workflow className="w-3.5 h-3.5" />
            <span>Agent Workflow</span>
          </button>
          <button
            onClick={() => setActiveTab('plan')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
              activeTab === 'plan'
                ? 'bg-[#C5A059] text-white shadow-xs'
                : 'text-stone-600 hover:text-stone-900 hover:bg-stone-50'
            }`}
          >
            <CalendarCheck className="w-3.5 h-3.5" />
            <span>Plan Blueprint</span>
          </button>
          <button
            onClick={() => setActiveTab('ask')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
              activeTab === 'ask'
                ? 'bg-[#C5A059] text-white shadow-xs'
                : 'text-stone-600 hover:text-stone-900 hover:bg-stone-50'
            }`}
          >
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Coach Q&A</span>
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
              activeTab === 'logs'
                ? 'bg-[#C5A059] text-white shadow-xs'
                : 'text-stone-600 hover:text-stone-900 hover:bg-stone-50'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Audit Trail</span>
          </button>
        </div>
      </div>

      {/* Backend Status / Error Banner */}
      {errorMessage && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium flex items-start justify-between gap-3 shadow-2xs animate-in fade-in">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-rose-900">Notice</p>
              <p className="mt-0.5 leading-relaxed">{errorMessage}</p>
              {promptInput && (
                <p className="mt-1 text-[11px] text-rose-700 font-normal">
                  Your prompt was preserved below so you can retry when ready.
                </p>
              )}
            </div>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-rose-500 hover:text-rose-800 text-xs font-bold px-1.5 py-0.5 rounded hover:bg-rose-100 transition-colors shrink-0"
            title="Dismiss notice"
          >
            ✕
          </button>
        </div>
      )}

      {statusNotice && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium flex items-start gap-3 shadow-2xs animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold text-emerald-900">Success</p>
            <p className="mt-0.5 leading-relaxed">{statusNotice}</p>
          </div>
        </div>
      )}

      {/* TAB 1: AUTONOMOUS AGENT WORKFLOW (PHASE 3 PRIMARY) */}
      {activeTab === 'agent' && (
        <div className="space-y-6">
          {/* Suggested Prompts Grid */}
          <div>
            <label className="block text-xs font-semibold text-stone-600 mb-2 flex items-center gap-1.5">
              <Lightbulb className="w-3.5 h-3.5 text-[#B08B44]" />
              <span>Suggested Agent Commands (Academic Demonstrations):</span>
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {SAMPLE_AGENT_PROMPTS.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => setPromptInput(item.prompt)}
                  className="text-left text-xs p-3 rounded-xl bg-white border border-[#EFEAE1] hover:border-[#D8C69F] hover:bg-[#FAF6F0] text-stone-700 font-medium transition-all shadow-2xs group flex items-start justify-between gap-2"
                >
                  <div className="min-w-0 flex-1">
                    <span className="text-[10px] font-bold text-[#A07C2F] uppercase block mb-0.5">
                      {item.category} • {item.badge}
                    </span>
                    <span className="text-stone-800 leading-snug">"{item.prompt}"</span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-stone-400 group-hover:text-[#B08B44] shrink-0 mt-1 transition-colors" />
                </button>
              ))}
            </div>
          </div>

          {/* Interactive Agent Input Box */}
          <Card className="p-3 sm:p-4">
            <form onSubmit={handleExecuteAgent} className="flex items-center gap-2">
              <input
                type="text"
                value={promptInput}
                onChange={(e) => setPromptInput(e.target.value)}
                disabled={isProcessing}
                placeholder="Give the Agent an instruction (e.g. 'Reschedule my missed sessions to open slots this week')..."
                className="flex-1 px-4 py-3 rounded-xl border border-stone-200 bg-stone-50/50 text-xs sm:text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white transition-all disabled:opacity-50"
              />
              <Button
                type="submit"
                variant="primary"
                disabled={isProcessing || !promptInput.trim()}
                icon={isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Bot className="w-4 h-4" />}
                className="shrink-0 px-4 sm:px-6 shadow-soft"
              >
                <span>{isProcessing ? 'Agent Thinking...' : 'Dispatch Agent'}</span>
              </Button>
            </form>
          </Card>

          {/* User Request Bubble */}
          {activeAgentQuery && (
            <div className="flex justify-end">
              <div className="max-w-xl bg-stone-900 text-white p-4 rounded-2xl rounded-tr-sm text-xs sm:text-sm shadow-soft">
                <p className="text-[10px] text-stone-400 font-semibold uppercase tracking-wider mb-1 flex items-center gap-1">
                  <span>Student Prompt</span>
                </p>
                <p className="font-medium">{activeAgentQuery}</p>
              </div>
            </div>
          )}

          {/* Processing Indicator */}
          {isProcessing && (
            <Card className="p-8 text-center border-dashed border-[#D8C69F] bg-[#FAF8F3]/60">
              <div className="flex flex-col items-center justify-center gap-3">
                <div className="w-12 h-12 rounded-full bg-[#FAF3E0] flex items-center justify-center text-[#B08B44] animate-pulse">
                  <Workflow className="w-6 h-6" />
                </div>
                <h4 className="text-sm font-semibold text-stone-900">
                  Executing Agent Decision Pipeline...
                </h4>
                <p className="text-xs text-stone-500 max-w-md">
                  Analyzing prompt intent, retrieving live database context, selecting agent tool, and verifying time constraints.
                </p>
              </div>
            </Card>
          )}

          {/* Agent Workflow Execution Steps */}
          {agentResult && !isProcessing && (
            <div className="space-y-6 animate-in fade-in">
              {/* Date, Timezone & Calendar Grounding Banner */}
              <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 rounded-2xl bg-[#FAF6F0] border border-[#E8D9B5] shadow-2xs">
                <div className="flex items-center gap-2 text-xs text-stone-700">
                  <Calendar className="w-4 h-4 text-[#B08B44]" />
                  <span className="font-semibold text-stone-900">Target Schedule Date:</span>
                  <span className="font-mono bg-white px-2 py-0.5 rounded-md border border-[#E8D9B5] text-stone-800 font-bold">
                    {agentResult.target_date || 'Next Available'}
                  </span>
                </div>
                {agentResult.timezone && (
                  <div className="flex items-center gap-1.5 text-xs text-stone-600">
                    <Globe className="w-3.5 h-3.5 text-[#B08B44]" />
                    <span className="text-[11px] font-mono bg-white px-2.5 py-0.5 rounded-md border border-[#E8D9B5] text-stone-700">
                      {agentResult.timezone}
                    </span>
                  </div>
                )}
              </div>

              {/* General Recommendation Notice (Empty-Database Mode) */}
              {agentResult.is_general_recommendation && (
                <div className="p-4 rounded-2xl bg-amber-50/90 border border-amber-200 text-amber-900 text-xs flex items-start gap-3 shadow-2xs">
                  <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold text-amber-950">General Schedule Blueprint</p>
                    <p className="mt-0.5 text-amber-800 leading-relaxed">
                      This daily schedule is formulated strictly from your provided prompt constraints. No active coursework or exams were linked from your database.
                    </p>
                  </div>
                </div>
              )}

              {/* Agent Assumptions & Grounding Notice */}
              {agentResult.assumptions && agentResult.assumptions.length > 0 && (
                <div className="p-4 rounded-2xl bg-stone-50 border border-stone-200 text-xs text-stone-700 shadow-2xs">
                  <p className="font-bold text-stone-900 mb-1.5 flex items-center gap-1.5">
                    <HelpCircle className="w-3.5 h-3.5 text-[#B08B44]" />
                    <span>Agent Assumptions & Grounding:</span>
                  </p>
                  <ul className="list-disc pl-5 space-y-1 text-stone-600">
                    {agentResult.assumptions.map((assump, aIdx) => (
                      <li key={aIdx}>{assump}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Constraint Violations Notice (When commitments exceed 24h or conflict) */}
              {agentResult.constraint_errors && agentResult.constraint_errors.length > 0 && (
                <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-800 shadow-2xs">
                  <p className="font-bold text-rose-900 mb-1 flex items-center gap-1.5">
                    <AlertCircle className="w-4 h-4 text-rose-600" />
                    <span>Constraint Conflicts Detected:</span>
                  </p>
                  <ul className="list-disc pl-5 space-y-1 text-rose-700">
                    {agentResult.constraint_errors.map((err, eIdx) => (
                      <li key={eIdx}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Pipeline Step Viewer */}
              <Card className="p-5 border-[#ECD9AF] bg-white">
                <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#F4ECE1]">
                  <div className="flex items-center gap-2">
                    <Workflow className="w-4 h-4 text-[#B08B44]" />
                    <h3 className="font-heading font-bold text-sm text-stone-900">
                      Explicit Agent Workflow Pipeline
                    </h3>
                  </div>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-stone-100 text-stone-600">
                    Tool: {agentResult.tool_name}
                  </span>
                </div>

                <div className="space-y-3">
                  {agentResult.steps.map((step) => (
                    <div
                      key={step.step_id}
                      className="p-3.5 rounded-xl border border-stone-100 bg-[#FAF9F5] flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-6 h-6 rounded-full bg-white border border-[#E8D9B5] text-[#8B6E30] text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                          {step.step_id}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-stone-900">
                              {step.name}
                            </span>
                          </div>
                          <p className="text-xs text-stone-600 mt-0.5 leading-relaxed">
                            {step.summary}
                          </p>
                        </div>
                      </div>
                      <div className="shrink-0 self-start sm:self-center">
                        {renderStepStatusBadge(step.status)}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Agent Explanation & Findings */}
              <Card className="p-5 border-stone-200 bg-white">
                <div className="flex items-center gap-2 mb-2 text-stone-900">
                  <Sparkles className="w-4 h-4 text-[#B08B44]" />
                  <h4 className="font-heading font-semibold text-sm">
                    {agentResult.summary}
                  </h4>
                </div>
                <div className="text-xs sm:text-sm text-stone-700 leading-relaxed whitespace-pre-line mt-1 bg-[#FAF8F3]/70 p-4 rounded-xl border border-[#EFEAE1]">
                  {agentResult.explanation}
                </div>
              </Card>

              {/* Safe Schedule Approval Card */}
              {agentResult.requires_approval && agentResult.proposed_sessions.length > 0 && (
                <Card className="p-5 border-amber-300 bg-gradient-to-b from-amber-50/50 to-white relative overflow-hidden shadow-soft">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 mb-4 border-b border-amber-200/80">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-lg bg-amber-100 border border-amber-300 flex items-center justify-center text-amber-800">
                        <ShieldCheck className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="font-heading font-bold text-sm text-stone-900">
                          Safe Schedule Approval: Proposed Session Modifications
                        </h4>
                        <p className="text-xs text-stone-600">
                          The agent has prepared {agentResult.proposed_sessions.length} event block(s). Only study sessions will be added to your planner timetable.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Proposed Sessions List with Multi-Event Styling */}
                  <div className="space-y-2.5 mb-5">
                    {agentResult.proposed_sessions.map((sess, sIdx) => {
                      const isExam = sess.event_type === 'exam';
                      const isSleep = sess.event_type === 'sleep';
                      const isMeal = sess.event_type === 'meal';
                      const isFixed = sess.event_type === 'fixed';

                      const borderBgClass = isExam
                        ? 'border-rose-300 bg-rose-50/40'
                        : isSleep
                        ? 'border-indigo-200 bg-indigo-50/30'
                        : isMeal
                        ? 'border-emerald-200 bg-emerald-50/30'
                        : isFixed
                        ? 'border-purple-200 bg-purple-50/30'
                        : 'border-[#E8D9B5] bg-white';

                      return (
                        <div
                          key={sIdx}
                          className={`p-3.5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs transition-all ${borderBgClass}`}
                        >
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                              {renderEventTypeBadge(sess.event_type)}
                              <span className="text-[11px] font-bold text-stone-800 bg-white/80 px-2 py-0.5 rounded-md border border-stone-200">
                                {sess.subject}
                              </span>
                              <span className="text-xs font-mono font-medium text-stone-600 flex items-center gap-1">
                                <Clock className="w-3 h-3 text-[#B08B44]" />
                                {sess.date} • {sess.start_time} - {sess.end_time} ({sess.duration_minutes}m)
                              </span>
                            </div>
                            <p className="text-xs font-semibold text-stone-900">{sess.topic}</p>
                            <p className="text-[11px] text-stone-600 mt-0.5 italic leading-relaxed">
                              Rationale: {sess.reason}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>


                  {/* Human-in-the-Loop Controls */}
                  {approvalDecision === null ? (
                    <div className="flex flex-col sm:flex-row items-center justify-end gap-3 pt-3 border-t border-amber-200">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={handleRejectProposal}
                        disabled={isRejecting || isApproving}
                        icon={isRejecting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <XCircle className="w-3.5 h-3.5 text-stone-500" />}
                        className="text-xs w-full sm:w-auto"
                      >
                        <span>{isRejecting ? 'Rejecting...' : 'Reject Changes'}</span>
                      </Button>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={handleApproveProposal}
                        disabled={isApproving || isRejecting}
                        icon={isApproving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5 text-white" />}
                        className="text-xs w-full sm:w-auto shadow-soft"
                      >
                        <span>{isApproving ? 'Saving Sessions...' : 'Approve & Add to Schedule'}</span>
                      </Button>
                    </div>
                  ) : approvalDecision === 'approved' ? (
                    <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span>Changes approved! Sessions are now saved to SQLite and active in your schedule.</span>
                    </div>
                  ) : (
                    <div className="p-3 rounded-xl bg-stone-100 border border-stone-200 text-stone-700 text-xs font-medium flex items-center gap-2">
                      <XCircle className="w-4 h-4 text-stone-500 shrink-0" />
                      <span>Changes discarded. Database was left untouched.</span>
                    </div>
                  )}
                </Card>
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: PLAN BLUEPRINT (PRESERVED PHASE 2) */}
      {activeTab === 'plan' && (
        <div className="space-y-4 pt-2">
          {/* Quick Input Bar */}
          <Card className="p-3 sm:p-4">
            <form onSubmit={handleSendPromptDirect} className="flex items-center gap-2">
              <input
                type="text"
                value={promptInput}
                onChange={(e) => setPromptInput(e.target.value)}
                disabled={isProcessing}
                placeholder="Type your study goal (e.g. 'Create a 5-day cramming plan for AI exam')..."
                className="flex-1 px-4 py-3 rounded-xl border border-stone-200 bg-stone-50/50 text-xs sm:text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white transition-all disabled:opacity-50"
              />
              <Button
                type="submit"
                variant="primary"
                disabled={isProcessing || !promptInput.trim()}
                icon={isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                className="shrink-0 px-4 sm:px-6 shadow-soft"
              >
                <span>{isProcessing ? 'Generating...' : 'Generate Plan'}</span>
              </Button>
            </form>
          </Card>

          {/* Plan Response Card or Empty State */}
          {!planResponse ? (
            <Card className="text-center py-12 px-6 border-dashed border-[#E5DECF] bg-white/60">
              <div className="w-12 h-12 rounded-full bg-[#FAF5EB] border border-[#E8DFC8] flex items-center justify-center mx-auto mb-3 text-[#B08B44]">
                <CalendarPlus className="w-6 h-6" />
              </div>
              <h3 className="font-heading font-bold text-stone-800 text-base mb-1">
                No Study Plan Generated Yet
              </h3>
              <p className="text-stone-500 text-xs sm:text-sm max-w-md mx-auto">
                Enter a study goal or exam target in the box above to generate an actionable, AI-powered revision plan with scheduled study blocks.
              </p>
            </Card>
          ) : (
            <Card className="border-[#ECD9AF] bg-white relative overflow-hidden">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 mb-4 border-b border-[#F4ECE1]">
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded-md border ${
                        isRealAiOutput
                          ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                          : 'bg-[#FAF3E0] text-[#9A7326] border-[#E8D9B5]'
                      }`}
                    >
                      {isRealAiOutput ? 'Gemini AI Generated' : 'Template Preview'}
                    </span>
                    <span className="text-xs text-stone-400 font-mono">
                      {planResponse.total_hours} total study hours
                    </span>
                  </div>
                  <h3 className="font-heading font-bold text-base text-stone-900 mt-1">
                    {planResponse.summary || 'Structured Study Blueprint'}
                  </h3>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleImportAll}
                    icon={<CalendarPlus className="w-3.5 h-3.5 text-[#B08B44]" />}
                    className="text-xs"
                  >
                    Import All to Schedule
                  </Button>
                </div>
              </div>

              <div className="space-y-3">
                {planResponse.blocks.map((block, idx) => {
                  const isAdded = addedBlocks[idx];

                  return (
                    <div
                      key={idx}
                      className={`p-4 rounded-xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                        isAdded
                          ? 'border-emerald-200 bg-emerald-50/40'
                          : 'border-[#EFEAE1] hover:border-[#D8C69F] bg-[#FAF8F3]/60'
                      }`}
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-[11px] font-bold text-[#8B6E30] bg-[#FAF4E6] px-2 py-0.5 rounded-md border border-[#ECDDBF]">
                            {block.subject}
                          </span>
                          <span className="text-xs font-mono font-medium text-stone-600 flex items-center gap-1">
                            <Clock className="w-3 h-3 text-[#B08B44]" />
                            {block.time} ({block.duration_minutes}m)
                          </span>
                          {block.priority && (
                            <span className="text-[10px] uppercase font-semibold text-stone-500">
                              • {block.priority} priority
                            </span>
                          )}
                        </div>

                        <h4 className="text-sm font-semibold text-stone-900 leading-snug">
                          {block.topic}
                        </h4>

                        {block.strategy && (
                          <p className="text-xs text-stone-600 mt-1 flex items-start gap-1.5">
                            <BookOpen className="w-3.5 h-3.5 text-stone-400 shrink-0 mt-0.5" />
                            <span><strong>Strategy:</strong> {block.strategy}</span>
                          </p>
                        )}

                        {block.break_recommendation && (
                          <p className="text-[11px] text-stone-500 mt-0.5 italic">
                            Break: {block.break_recommendation}
                          </p>
                        )}
                      </div>

                      <Button
                        variant={isAdded ? 'outline' : 'secondary'}
                        size="sm"
                        onClick={() => handleImportBlock(block, idx)}
                        icon={isAdded ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <CalendarPlus className="w-3.5 h-3.5 text-[#B08B44]" />}
                        disabled={isAdded}
                        className="text-xs shrink-0 self-end sm:self-auto"
                      >
                        {isAdded ? 'Imported' : 'Add to Schedule'}
                      </Button>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* TAB 3: COACH Q&A (PRESERVED PHASE 2) */}
      {activeTab === 'ask' && (
        <div className="space-y-4 pt-2">
          {/* Quick Input Bar */}
          <Card className="p-3 sm:p-4">
            <form onSubmit={handleSendPromptDirect} className="flex items-center gap-2">
              <input
                type="text"
                value={promptInput}
                onChange={(e) => setPromptInput(e.target.value)}
                disabled={isProcessing}
                placeholder="Ask anything about revision techniques, exam prep, or time management..."
                className="flex-1 px-4 py-3 rounded-xl border border-stone-200 bg-stone-50/50 text-xs sm:text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-[#C5A059] focus:bg-white transition-all disabled:opacity-50"
              />
              <Button
                type="submit"
                variant="primary"
                disabled={isProcessing || !promptInput.trim()}
                icon={isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                className="shrink-0 px-4 sm:px-6 shadow-soft"
              >
                <span>{isProcessing ? 'Thinking...' : 'Ask Coach'}</span>
              </Button>
            </form>
          </Card>

          {askHistory.length === 0 ? (
            <Card className="py-12 text-center">
              <div className="w-12 h-12 rounded-full bg-[#FAF3E0] flex items-center justify-center mx-auto mb-2 text-[#C5A059]">
                <HelpCircle className="w-6 h-6 text-[#B08B44]" />
              </div>
              <h3 className="font-heading font-semibold text-stone-900 text-sm">
                Ask your Academic Coach
              </h3>
              <p className="text-xs text-stone-500 mt-1 max-w-md mx-auto">
                Need study tips, memory hacks, or help balancing tough coursework? Ask above to get tailored coaching powered by Gemini AI.
              </p>
            </Card>
          ) : (
            <div className="space-y-4">
              {askHistory.map((item, idx) => (
                <div key={idx} className="space-y-3">
                  <div className="flex justify-end">
                    <div className="max-w-xl bg-stone-900 text-white p-3.5 rounded-2xl rounded-tr-sm text-xs sm:text-sm shadow-soft">
                      <p className="text-[10px] text-stone-400 font-semibold uppercase tracking-wider mb-1">
                        Question
                      </p>
                      <p className="font-medium">{item.q}</p>
                    </div>
                  </div>

                  <Card className="border-[#ECD9AF] bg-white p-5">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-6 h-6 rounded-md bg-[#FAF3E0] flex items-center justify-center text-[#B08B44]">
                        <Sparkles className="w-3.5 h-3.5" />
                      </div>
                      <span className="text-xs font-bold text-stone-900">
                        Academic Coach Response
                      </span>
                    </div>

                    <div className="text-xs sm:text-sm text-stone-700 leading-relaxed whitespace-pre-line mt-2">
                      {item.a.answer}
                    </div>

                    {item.a.suggested_actions && item.a.suggested_actions.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-[#F4ECE1]">
                        <p className="text-[11px] font-semibold uppercase tracking-wider text-stone-500 mb-2">
                          Recommended Action Steps
                        </p>
                        <div className="space-y-1.5">
                          {item.a.suggested_actions.map((act, actIdx) => (
                            <div key={actIdx} className="flex items-start gap-2 text-xs text-stone-700">
                              <CheckCircle2 className="w-3.5 h-3.5 text-[#B08B44] shrink-0 mt-0.5" />
                              <span>{act}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </Card>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 4: AGENT AUDIT LOGS */}
      {activeTab === 'logs' && (
        <div className="space-y-4 pt-2">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-heading font-semibold text-stone-900">
              Agent Activity Audit Trail
            </h3>
            <Button
              variant="secondary"
              size="sm"
              onClick={fetchLogs}
              disabled={isLoadingLogs}
              icon={<RefreshCw className={`w-3.5 h-3.5 ${isLoadingLogs ? 'animate-spin' : ''}`} />}
              className="text-xs"
            >
              Refresh
            </Button>
          </div>

          {isLoadingLogs ? (
            <Card className="p-8 text-center text-xs text-stone-500">
              <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-[#B08B44]" />
              Loading audit logs...
            </Card>
          ) : activityLogs.length === 0 ? (
            <Card className="p-8 text-center text-xs text-stone-500">
              No agent activity recorded yet. Run an agent command in the Agent Workflow tab to log operations.
            </Card>
          ) : (
            <div className="space-y-2.5">
              {activityLogs.map((log) => (
                <Card key={log.id} className="p-4 border-[#EFEAE1] hover:border-[#D8C69F] transition-all">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-100 text-stone-700 font-semibold uppercase">
                        {log.action_type}
                      </span>
                      <span className="text-[11px] font-mono text-stone-500">
                        tool: {log.tool_name}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase border ${
                          log.status === 'success' || log.status === 'approved'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : log.status === 'rejected'
                            ? 'bg-amber-50 text-amber-700 border-amber-200'
                            : 'bg-rose-50 text-rose-700 border-rose-200'
                        }`}
                      >
                        {log.status}
                      </span>
                      {log.created_at && (
                        <span className="text-[10px] font-mono text-stone-400">
                          {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      )}
                    </div>
                  </div>
                  <p className="text-xs text-stone-800 leading-snug">{log.summary}</p>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
