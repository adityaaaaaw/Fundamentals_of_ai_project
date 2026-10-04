import json
import logging
import httpx
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status
from google import genai
from google.genai import types
from app.core.config import settings
from app.schemas.ai import (
    GeneratePlanRequest,
    GeneratePlanResponse,
    AskRequest,
    AskResponse,
    OptimizeScheduleRequest,
    OptimizeScheduleResponse,
    StudyBlock,
)

logger = logging.getLogger(__name__)


def get_gemini_client() -> genai.Client:
    api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""
    if not api_key or api_key == "your_gemini_api_key":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API key is not configured. Please set GEMINI_API_KEY in backend/.env to use AI features."
        )
    timeout_sec = getattr(settings, "GEMINI_REQUEST_TIMEOUT_SECONDS", 15.0)
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            client_args={"timeout": httpx.Timeout(timeout_sec, connect=10.0)}
        )
    )


def handle_gemini_error(e: Exception, action_name: str) -> HTTPException:
    """Map Gemini errors to clear, structured HTTP exceptions."""
    if isinstance(e, HTTPException):
        return e

    error_str = str(e)
    status_code = getattr(e, "code", getattr(e, "status_code", None))

    if "429" in error_str or status_code == 429 or "RESOURCE_EXHAUSTED" in error_str:
        logger.warning(f"Gemini rate limit exceeded in {action_name}: {error_str}")
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Gemini API rate limit reached. Please wait a moment before trying again."
        )
    if "503" in error_str or status_code == 503 or "high demand" in error_str.lower():
        logger.warning(f"Gemini high demand/unavailable in {action_name}: {error_str}")
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI model is temporarily experiencing high demand. Please try again in a few moments."
        )
    if "timeout" in error_str.lower() or "deadline" in error_str.lower() or status_code == 504:
        logger.warning(f"Gemini request timeout in {action_name}: {error_str}")
        return HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Gemini API request timed out after 15 seconds. Please try again."
        )
    if "401" in error_str or "403" in error_str or "API_KEY_INVALID" in error_str or "PERMISSION_DENIED" in error_str:
        logger.error(f"Gemini authentication/permission error in {action_name}: {error_str}")
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Gemini API authentication failed. Please verify that your GEMINI_API_KEY in backend/.env is valid."
        )
    if "400" in error_str or "INVALID_ARGUMENT" in error_str:
        logger.error(f"Gemini invalid argument in {action_name}: {error_str}")
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request sent to AI model."
        )

    logger.error(f"Unexpected Gemini API error during {action_name}: {error_str}")
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"AI service encountered an unexpected error: {error_str}"
    )


def generate_content_with_resilience(
    client: genai.Client,
    contents: Any,
    config: Optional[types.GenerateContentConfig] = None,
    action_name: str = "ai_operation"
) -> Tuple[Any, str]:
    """Execute Gemini call with fallback ONLY for transient model availability errors (503/504)."""
    primary_model = settings.GEMINI_MODEL
    models = [primary_model]
    if primary_model == "gemini-3.5-flash-lite" and "gemini-3.5-flash" not in models:
        models.append("gemini-3.5-flash")
    elif primary_model == "gemini-3.5-flash" and "gemini-3.5-flash-lite" not in models:
        models.append("gemini-3.5-flash-lite")

    last_err = None
    for idx, model_id in enumerate(models):
        try:
            resp = client.models.generate_content(
                model=model_id,
                contents=contents,
                config=config,
            )
            return resp, model_id
        except HTTPException:
            raise
        except Exception as e:
            last_err = e
            err_str = str(e)
            status_code = getattr(e, "code", getattr(e, "status_code", None))
            # Fallback ONLY on transient model availability errors (503, 504, high demand, timeout)
            # NEVER fallback on 400, 401, 403, 404
            is_transient = (
                "503" in err_str or
                "504" in err_str or
                "high demand" in err_str.lower() or
                "timeout" in err_str.lower() or
                status_code in (503, 504)
            )
            if is_transient and idx < len(models) - 1:
                logger.warning(f"Transient error on {model_id}. Failing over to {models[idx+1]}...")
                continue
            raise handle_gemini_error(e, action_name)
    raise handle_gemini_error(last_err, action_name)


def _clean_json_text(text: str) -> str:
    """Clean markdown code fence wrapper if present."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def generate_study_plan(request: GeneratePlanRequest, context_data: Optional[Dict[str, Any]] = None) -> GeneratePlanResponse:
    client = get_gemini_client()

    prompt = f"""
You are an expert AI academic advisor and study planner for university students.
The student has submitted the following study goal:
Goal: "{request.goal}"
Subject preference: "{request.subject or 'General coursework'}"
Target Date: "{request.target_date or 'Next few days'}"
Available Study Hours: {request.available_hours or 'Flexible (suggest appropriate duration)'}
Preferred Session Duration: {request.preferred_duration or 60} minutes
Additional Instructions: {request.instructions or 'None'}

Student's active academic context:
{json.dumps(context_data or {}, indent=2)}

Generate a structured, actionable study schedule with prioritized focus blocks, realistic rest breaks, and active-recall strategies.

You MUST respond with ONLY a valid JSON object matching this schema:
{{
  "goal": "{request.goal}",
  "summary": "Brief encouraging summary explaining the schedule rationale",
  "total_hours": 3.5,
  "blocks": [
    {{
      "time": "09:00 - 10:30",
      "start_time": "09:00",
      "end_time": "10:30",
      "subject": "Fundamentals of AI",
      "topic": "Minimax with Alpha-Beta Pruning Practice",
      "duration_minutes": 90,
      "strategy": "Solve 3 minimax game tree problems by hand before checking implementation.",
      "break_recommendation": "10-minute stretch & eye rest",
      "priority": "high"
    }}
  ]
}}
Do not include any commentary outside the JSON object.
"""

    try:
        response, _ = generate_content_with_resilience(
            client=client,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
            ),
            action_name="generate_study_plan"
        )
        cleaned_text = _clean_json_text(response.text or "{}")
        data = json.loads(cleaned_text)
        return GeneratePlanResponse.model_validate(data)
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Malformed JSON from Gemini: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Received malformed study plan format from AI service. Please try again."
        )
    except Exception as e:
        raise handle_gemini_error(e, "generate_study_plan")


def ask_study_assistant(request: AskRequest, context_data: Optional[Dict[str, Any]] = None) -> AskResponse:
    client = get_gemini_client()

    prompt = f"""
You are a warm, supportive, and highly knowledgeable AI Study Assistant for college students.
Student question: "{request.question}"

Additional Context:
{request.context or ''}
Active Student Coursework Data:
{json.dumps(context_data or {}, indent=2)}

Provide a concise, practical, and highly pedagogical answer. Recommend 2 to 3 concrete next action steps.

Respond with ONLY a valid JSON object matching:
{{
  "answer": "Detailed helpful explanation and advice formatted with clear paragraphs or bullet points",
  "suggested_actions": ["Review lecture slides on eigenvalues", "Schedule a 45-min practice block", "Summarize notes using Feynman technique"]
}}
"""

    try:
        response, _ = generate_content_with_resilience(
            client=client,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.4,
            ),
            action_name="ask_study_assistant"
        )
        cleaned_text = _clean_json_text(response.text or "{}")
        data = json.loads(cleaned_text)
        return AskResponse.model_validate(data)
    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Received malformed answer from AI service. Please try again."
        )
    except Exception as e:
        raise handle_gemini_error(e, "ask_study_assistant")


def optimize_schedule(request: OptimizeScheduleRequest, context_data: Optional[Dict[str, Any]] = None) -> OptimizeScheduleResponse:
    client = get_gemini_client()

    prompt = f"""
You are an expert timetable scheduling AI.
Optimize the student's study timetable for:
Target Date: "{request.target_date or 'Upcoming week'}"
Available Study Hours: {request.available_hours or 4.0}
Preferences: "{request.preferences or 'Balanced workload'}"

Student's existing commitments and deadlines:
{json.dumps(context_data or {}, indent=2)}

Generate non-overlapping, balanced study blocks that prioritize impending deadlines and exams.

Respond with ONLY a valid JSON object matching:
{{
  "summary": "Summary of schedule adjustments made to optimize focus and avoid burnout",
  "recommendations": [
    {{
      "time": "14:00 - 15:30",
      "start_time": "14:00",
      "end_time": "15:30",
      "subject": "Linear Algebra",
      "topic": "Orthogonal Projections & QR Decomposition",
      "duration_minutes": 90,
      "strategy": "Solve 4 theorem proofs and numerical exercises",
      "break_recommendation": "15-minute walk outside",
      "priority": "high"
    }}
  ]
}}
"""

    try:
        response, _ = generate_content_with_resilience(
            client=client,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
            ),
            action_name="optimize_schedule"
        )
        cleaned_text = _clean_json_text(response.text or "{}")
        data = json.loads(cleaned_text)
        return OptimizeScheduleResponse.model_validate(data)
    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Received malformed schedule optimization from AI service. Please try again."
        )
    except Exception as e:
        raise handle_gemini_error(e, "optimize_schedule")
