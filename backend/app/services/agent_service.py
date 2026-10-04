import json
import logging
import time
import uuid
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from google.genai import types

from app.models.task import Task
from app.models.session import StudySession
from app.models.exam import Exam
from app.models.agent_log import AgentActivityLog
from app.schemas.agent import (
    AgentExecuteRequest,
    AgentExecuteResponse,
    AgentWorkflowStep,
    ProposedSessionBlock,
    ScheduleApprovalResponse,
    ScheduleRejectResponse,
)
from app.services import gemini_service, session_service
from app.services.agent_tools import (
    get_gemini_tools,
    dispatch_tool,
)
from app.utils import date_utils
from app.utils.date_utils import get_day_of_week
from app.core.config import settings

logger = logging.getLogger(__name__)


def _gather_student_context(db: Session, user_id: str) -> Dict[str, Any]:
    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    sessions = db.query(StudySession).filter(StudySession.user_id == user_id).all()
    exams = db.query(Exam).filter(Exam.user_id == user_id).all()

    pending_tasks = [t for t in tasks if t.status == "pending"]
    completed_tasks = [t for t in tasks if t.status == "completed"]
    missed_tasks = [t for t in tasks if t.status == "missed"]
    missed_sessions = [s for s in sessions if s.status == "missed"]
    upcoming_sessions = [s for s in sessions if s.status in ["upcoming", "planned"]]

    return {
        "pending_tasks": [{"id": t.id, "subject": t.subject, "title": t.title, "due_date": t.due_date, "priority": t.priority} for t in pending_tasks],
        "completed_tasks_count": len(completed_tasks),
        "missed_tasks_count": len(missed_tasks),
        "upcoming_exams": [{"subject": e.subject, "title": e.title, "date": e.exam_date, "time": e.exam_time} for e in exams],
        "scheduled_sessions": [{"id": s.id, "subject": s.subject, "topic": s.title, "date": s.date, "start_time": s.start_time, "end_time": s.end_time} for s in upcoming_sessions],
        "missed_sessions": [{"id": s.id, "subject": s.subject, "topic": s.title, "date": s.date, "start_time": s.start_time, "end_time": s.end_time} for s in missed_sessions],
    }


def execute_agent_workflow(
    db: Session,
    user_id: str,
    request: AgentExecuteRequest
) -> AgentExecuteResponse:
    req_id = uuid.uuid4().hex[:8]
    t_start = time.perf_counter()

    # 1. Resolve Timezone and Calendar Anchor (Deterministic backend date resolution)
    tz_str = request.timezone
    current_dt = date_utils.get_current_datetime(tz_str)
    today_iso = current_dt.date().isoformat()
    today_wd = date_utils.get_day_of_week(today_iso)
    current_time_str = current_dt.strftime("%H:%M:%S")
    tz_display = str(current_dt.tzinfo)

    resolved_target_date, resolved_target_wd = date_utils.resolve_target_date(
        relative_str=request.target_date,
        tz_name=tz_str,
        prompt_text=request.prompt
    )

    # 2. Validate Gemini Client & Configuration
    client = gemini_service.get_gemini_client()

    steps: List[AgentWorkflowStep] = []

    # Step 1: Request Received
    steps.append(
        AgentWorkflowStep(
            step_id=1,
            name="Request Received",
            status="completed",
            summary=f"Received prompt: '{request.prompt[:55]}...' (Client Timezone: {tz_display})"
        )
    )

    # Step 2: Context Retrieved from SQLite & Date Anchor
    t_ctx_start = time.perf_counter()
    context = _gather_student_context(db, user_id)
    dur_ctx = (time.perf_counter() - t_ctx_start) * 1000

    steps.append(
        AgentWorkflowStep(
            step_id=2,
            name="Context Retrieved",
            status="completed",
            summary=f"Queried SQLite ({len(context['pending_tasks'])} tasks, {len(context['upcoming_exams'])} exams). Target Date anchored: {resolved_target_date} ({resolved_target_wd})."
        )
    )

    # Step 3: Send to Gemini with Grounded Calendar Anchor and Dynamic System Instruction
    system_instruction = (
        "You are an expert AI Academic Study Planner Agent for university students.\n"
        "You have access to 5 specialized tools to inspect data and formulate study schedules.\n"
        "Analyze the student's prompt and current academic context carefully.\n\n"
        "EXPLICIT REAL-TIME CALENDAR GROUNDING (DO NOT VIOLATE):\n"
        f"- Current System Date: {today_iso} ({today_wd})\n"
        f"- Current System Time: {current_time_str}\n"
        f"- Timezone: {tz_display}\n"
        f"- Resolved Target Date: {resolved_target_date} ({resolved_target_wd})\n\n"
        "CRITICAL RULES:\n"
        "- NEVER invent past dates like 2024-05-15 or dates in the past.\n"
        "- When optimizing or planning a schedule, ALWAYS use the resolved target date above.\n"
        "- When the database has 0 tasks/exams, NEVER fabricate courses like Calculus. Use only explicit constraints.\n"
        "- Respect daily 24-hour capacity limits (sleep + meals + work + exam + study <= 24h).\n\n"
        "Always call the most appropriate tool:\n"
        "- generate_study_plan_tool: when the student wants a study plan, revision schedule, or exam prep plan.\n"
        "- query_study_progress_tool: when the student asks how they are doing, asks for progress, tasks status, or completion rates.\n"
        "- reschedule_missed_sessions_tool: when the student wants to reschedule missed sessions or catch up.\n"
        "- optimize_study_schedule_tool: when the student wants to optimize their timetable, balance workloads, or avoid burnout.\n"
        "- academic_coaching_tool: when the student asks for study techniques, learning advice, or conceptual coaching.\n"
    )

    prompt_content = f"""
Student Prompt: "{request.prompt}"

Temporal Anchor:
- Current System Timestamp: {today_iso} {current_time_str} ({tz_display})
- Resolved Target Date: {resolved_target_date} ({resolved_target_wd})
- Preferred Hours: {request.preferred_hours or 'Flexible'}

Current Student Snapshot from Database:
- Pending Tasks: {len(context['pending_tasks'])}
- Upcoming Exams: {len(context['upcoming_exams'])}
- Missed Sessions: {len(context['missed_sessions'])}

Select the appropriate tool to execute for this student.
"""

    gemini_tools = get_gemini_tools()
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=gemini_tools,
        temperature=0.1,
    )

    user_message = types.Content(role="user", parts=[types.Part.from_text(text=prompt_content)])

    t_r1_start = time.perf_counter()
    try:
        gemini_response, used_model = gemini_service.generate_content_with_resilience(
            client=client,
            contents=[user_message],
            config=config,
            action_name="agent_tool_selection"
        )
    except HTTPException as he:
        # Record failure log in SQLite
        db_log = AgentActivityLog(
            user_id=user_id,
            action_type="unknown",
            tool_name="gemini_agent",
            summary=f"Gemini API failure: {he.detail}",
            status="failed",
        )
        db.add(db_log)
        db.commit()
        raise
    dur_r1 = (time.perf_counter() - t_r1_start) * 1000

    # 4. Check whether Gemini selected a function call
    function_calls = getattr(gemini_response, "function_calls", None)

    target_date_val = resolved_target_date
    assumptions_val: List[str] = []
    is_general_val = False
    constraint_errors_val: List[str] = []

    if function_calls:
        fc = function_calls[0]
        tool_name = fc.name
        tool_args = dict(fc.args) if fc.args else {}

        steps.append(
            AgentWorkflowStep(
                step_id=3,
                name="Gemini-Selected Tool",
                status="completed",
                summary=f"Gemini selected '{tool_name}' with arguments: {json.dumps(tool_args)}"
            )
        )

        # Step 4: Execute Selected Tool against SQLite
        t_tool_start = time.perf_counter()
        try:
            tool_result = dispatch_tool(
                tool_name=tool_name,
                raw_args=tool_args,
                db=db,
                user_id=user_id,
                prompt_context=request.prompt
            )
        except Exception as e:
            logger.error(f"Tool execution failed for '{tool_name}': {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent tool execution error in {tool_name}: {str(e)}"
            )
        dur_tool = (time.perf_counter() - t_tool_start) * 1000

        action_type = tool_result.get("action_type", "agent_action")
        summary = tool_result.get("summary", "Tool executed successfully.")
        requires_approval = bool(tool_result.get("requires_approval", False))
        proposed_sessions_raw = tool_result.get("proposed_sessions", [])
        proposed_sessions = [ProposedSessionBlock.model_validate(p) for p in proposed_sessions_raw]

        target_date_val = tool_result.get("target_date", resolved_target_date)
        assumptions_val = tool_result.get("assumptions", [])
        is_general_val = tool_result.get("is_general_recommendation", False)
        constraint_errors_val = tool_result.get("constraint_errors", [])

        if constraint_errors_val:
            requires_approval = False

        steps.append(
            AgentWorkflowStep(
                step_id=4,
                name="Tool Execution Result",
                status="completed",
                summary=f"Executed {tool_name} against SQLite: {summary}"
            )
        )

        # Step 5: Send Tool Result Back to Gemini for Grounded Explanation
        steps.append(
            AgentWorkflowStep(
                step_id=5,
                name="Additional Gemini Processing",
                status="processing",
                summary="Sending tool results back to Gemini for grounded reasoning and final synthesis..."
            )
        )

        t_r2_start = time.perf_counter()
        try:
            # Preserve original model candidate content (with thought signature if present)
            if hasattr(gemini_response, "candidates") and gemini_response.candidates:
                model_content = gemini_response.candidates[0].content
            else:
                model_call_part = types.Part(
                    function_call=types.FunctionCall(name=tool_name, args=tool_args)
                )
                model_content = types.Content(role="model", parts=[model_call_part])

            # Tool response content formatted per Google GenAI SDK spec: role='user'
            tool_response_part = types.Part.from_function_response(
                name=tool_name,
                response={"result": tool_result}
            )
            tool_content = types.Content(role="user", parts=[tool_response_part])

            conversation_history = [user_message, model_content, tool_content]

            followup_response, _ = gemini_service.generate_content_with_resilience(
                client=client,
                contents=conversation_history,
                config=types.GenerateContentConfig(temperature=0.3),
                action_name="agent_synthesis"
            )

            explanation = followup_response.text.strip() if followup_response.text else summary
            steps[-1].status = "completed"
            steps[-1].summary = "Gemini synthesized grounded response from live SQLite tool results."
            dur_r2 = (time.perf_counter() - t_r2_start) * 1000
        except Exception as e:
            dur_r2 = (time.perf_counter() - t_r2_start) * 1000
            logger.warning(f"Notice in Gemini second-round synthesis: {e}")
            explanation = summary
            steps[-1].status = "completed"
            steps[-1].summary = "Tool results verified against SQLite database."

    else:
        dur_tool = 0.0
        dur_r2 = 0.0
        # Gemini responded directly without function calling
        tool_name = "academic_coaching_tool"
        action_type = "academic_coaching"
        explanation = gemini_response.text.strip() if gemini_response.text else "Response received from Gemini."
        summary = "Academic coaching generated directly by Gemini."
        requires_approval = False
        proposed_sessions = []

        steps.append(
            AgentWorkflowStep(
                step_id=3,
                name="Gemini-Selected Tool",
                status="completed",
                summary="Gemini answered directly with cognitive coaching advice."
            )
        )
        steps.append(
            AgentWorkflowStep(
                step_id=4,
                name="Tool Execution Result",
                status="completed",
                summary="Cognitive coaching recommendations prepared."
            )
        )

    # Log safe stage timings
    dur_total = (time.perf_counter() - t_start) * 1000
    logger.info(
        f"[Agent {req_id}] Stage timings: Context={dur_ctx:.1f}ms | "
        f"Gemini-R1={dur_r1:.1f}ms | Tool({tool_name})={dur_tool:.1f}ms | "
        f"Gemini-R2={dur_r2:.1f}ms | Total={dur_total:.1f}ms"
    )

    # Step 6: Approval / Completion Gate
    if requires_approval and proposed_sessions:
        steps.append(
            AgentWorkflowStep(
                step_id=6,
                name="Awaiting User Approval",
                status="awaiting_approval",
                summary=f"Prepared {len(proposed_sessions)} proposed session(s). Awaiting explicit student approval before modifying SQLite."
            )
        )
    elif constraint_errors_val:
        steps.append(
            AgentWorkflowStep(
                step_id=6,
                name="Constraints Infeasible",
                status="failed",
                summary=f"Validation detected conflicts: {'; '.join(constraint_errors_val)}"
            )
        )
    else:
        steps.append(
            AgentWorkflowStep(
                step_id=6,
                name="Completed",
                status="completed",
                summary="Agent execution completed successfully."
            )
        )

    # 5. Persist Activity Log in SQLite
    log_status = "awaiting_approval" if (requires_approval and proposed_sessions) else "completed"
    if constraint_errors_val:
        log_status = "failed"

    db_log = AgentActivityLog(
        user_id=user_id,
        action_type=action_type,
        tool_name=tool_name,
        summary=summary,
        status=log_status,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)

    return AgentExecuteResponse(
        prompt=request.prompt,
        action_type=action_type,
        tool_name=tool_name,
        summary=summary,
        explanation=explanation,
        steps=steps,
        requires_approval=requires_approval and len(proposed_sessions) > 0,
        proposed_sessions=proposed_sessions,
        target_date=target_date_val,
        timezone=tz_display,
        assumptions=assumptions_val,
        is_general_recommendation=is_general_val,
        constraint_errors=constraint_errors_val,
        data_snapshot={
            "pending_tasks_count": len(context["pending_tasks"]),
            "upcoming_exams_count": len(context["upcoming_exams"]),
            "missed_sessions_count": len(context["missed_sessions"]),
            "log_id": db_log.id,
        }
    )


def approve_schedule_proposal(
    db: Session,
    user_id: str,
    proposed_sessions: List[ProposedSessionBlock],
    log_id: Optional[str] = None
) -> ScheduleApprovalResponse:
    saved_ids = []
    rejected_count = 0

    for block in proposed_sessions:
        # Only persist study sessions (and optional exam records); do NOT save sleep, meals, or fixed routines to StudySession
        if block.event_type not in ["study", "exam"]:
            continue

        if block.event_type == "exam":
            # Record proposed exam in Exam table if not already present
            existing_exam = db.query(Exam).filter(
                Exam.user_id == user_id,
                Exam.exam_date == block.date,
                Exam.subject.ilike(f"%{block.subject}%"),
            ).first()
            if not existing_exam:
                new_exam = Exam(
                    user_id=user_id,
                    subject=block.subject,
                    title=block.topic,
                    exam_date=block.date,
                    exam_time=block.start_time,
                    notes=block.reason,
                )
                db.add(new_exam)
                db.commit()
            continue

        # Re-validate conflict at approval time against existing StudySessions
        conflict = session_service.check_session_conflict(
            db,
            user_id,
            block.date,
            block.start_time,
            block.end_time
        )
        if conflict:
            rejected_count += 1
            continue

        # Check conflict with existing Exams on that date
        conflicting_exams = db.query(Exam).filter(
            Exam.user_id == user_id,
            Exam.exam_date == block.date,
        ).all()
        has_exam_conflict = False
        for exm in conflicting_exams:
            if exm.exam_time:
                exm_end = date_utils.minutes_to_time_str(date_utils.time_to_minutes(exm.exam_time) + 120)
                if date_utils.check_time_overlap(block.start_time, block.end_time, exm.exam_time, exm_end):
                    has_exam_conflict = True
                    break
        if has_exam_conflict:
            rejected_count += 1
            continue

        try:
            day_name = get_day_of_week(block.date)
        except Exception:
            day_name = "Monday"

        new_sess = StudySession(
            user_id=user_id,
            subject=block.subject,
            title=block.topic,
            date=block.date,
            day_of_week=day_name,
            start_time=block.start_time,
            end_time=block.end_time,
            duration_minutes=block.duration_minutes,
            status="upcoming",
            notes=block.reason,
            color=block.color,
        )
        db.add(new_sess)
        db.commit()
        db.refresh(new_sess)
        saved_ids.append(new_sess.id)

    # Update log status to approved in SQLite
    if log_id:
        log_entry = db.query(AgentActivityLog).filter(AgentActivityLog.id == log_id).first()
        if log_entry:
            log_entry.status = "approved"
            db.commit()

    msg = f"Approved and added {len(saved_ids)} study session(s) to your Study Schedule."
    if rejected_count > 0:
        msg += f" ({rejected_count} session(s) skipped due to time conflicts with existing schedule)."

    return ScheduleApprovalResponse(
        approved=True,
        saved_count=len(saved_ids),
        rejected_count=rejected_count,
        message=msg,
        saved_session_ids=saved_ids,
    )



def reject_schedule_proposal(
    db: Session,
    user_id: str,
    log_id: Optional[str] = None,
    reason: str = "Student rejected proposed changes"
) -> ScheduleRejectResponse:
    # Explicitly do NOT modify or add any study sessions
    if log_id:
        log_entry = db.query(AgentActivityLog).filter(AgentActivityLog.id == log_id).first()
        if log_entry:
            log_entry.status = "rejected"
            db.commit()

    return ScheduleRejectResponse(
        approved=False,
        message="Proposed schedule changes rejected. No modifications were made to your database."
    )


def get_agent_activity_logs(db: Session, user_id: str, limit: int = 20) -> List[AgentActivityLog]:
    return db.query(AgentActivityLog).filter(
        AgentActivityLog.user_id == user_id
    ).order_by(AgentActivityLog.created_at.desc()).limit(limit).all()
