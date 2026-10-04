from unittest.mock import MagicMock, patch
from app.models.session import StudySession
from app.models.task import Task
from app.core.config import settings


def _create_mock_gemini_client(tool_name: str, tool_args: dict, final_explanation: str = "Analysis complete."):
    """Helper to create a mock Gemini client with realistic 2-stage tool calling."""
    # Round 1: Model returns a function call
    mock_fc = MagicMock()
    mock_fc.name = tool_name
    mock_fc.args = tool_args

    mock_resp_round1 = MagicMock()
    mock_resp_round1.function_calls = [mock_fc]

    # Round 2: Model returns grounded explanation text
    mock_resp_round2 = MagicMock()
    mock_resp_round2.function_calls = None
    mock_resp_round2.text = final_explanation

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = [mock_resp_round1, mock_resp_round2]
    return mock_client


def test_agent_missing_key_returns_503(client):
    with patch.object(settings, "GEMINI_API_KEY", ""):
        res = client.post("/api/v1/ai/agent/execute", json={"prompt": "Generate a study plan"})
        assert res.status_code == 503
        assert "not configured" in res.json()["detail"].lower()


def test_agent_workflow_generates_plan_with_steps(client):
    mock_client = _create_mock_gemini_client(
        tool_name="generate_study_plan_tool",
        tool_args={"goal": "AI Midterm Revision", "subject": "Fundamentals of AI"},
        final_explanation="I have created a focused 3-day revision timetable for your AI Midterm."
    )

    with patch.object(settings, "GEMINI_API_KEY", "mock-key"):
        with patch("app.services.gemini_service.get_gemini_client", return_value=mock_client):
            res = client.post("/api/v1/ai/agent/execute", json={"prompt": "Generate a revision plan for AI Midterm"})
            assert res.status_code == 200
            data = res.json()
            assert "steps" in data
            assert len(data["steps"]) >= 5
            assert data["tool_name"] == "generate_study_plan_tool"
            assert data["action_type"] == "generate_plan"
            assert data["requires_approval"] is True
            assert len(data["proposed_sessions"]) >= 1
            assert "AI Midterm" in data["summary"]
            assert "focused 3-day revision" in data["explanation"]


def test_agent_progress_query(client, db_session):
    # Seed real task into SQLite
    task = Task(
        title="Test Lab Assignment",
        subject="Fundamentals of AI",
        due_date="2026-10-12",
        priority="high",
        status="pending",
        user_id=settings.DEMO_USER_ID,
    )
    db_session.add(task)
    db_session.commit()

    mock_client = _create_mock_gemini_client(
        tool_name="query_study_progress_tool",
        tool_args={"query_focus": "general"},
        final_explanation="You have 1 pending task and are making steady progress."
    )

    with patch.object(settings, "GEMINI_API_KEY", "mock-key"):
        with patch("app.services.gemini_service.get_gemini_client", return_value=mock_client):
            res = client.post("/api/v1/ai/agent/execute", json={"prompt": "How am I doing on my study progress?"})
            assert res.status_code == 200
            data = res.json()
            assert data["tool_name"] == "query_study_progress_tool"
            assert data["action_type"] == "query_progress"
            assert "completion rate" in data["summary"].lower()
            assert data["requires_approval"] is False
            assert len(data["proposed_sessions"]) == 0


def test_agent_reschedule_missed_sessions(client, db_session):
    # Seed a missed session into SQLite
    missed_session = StudySession(
        user_id=settings.DEMO_USER_ID,
        subject="Database Systems",
        title="Missed B+ Tree Lecture",
        date="2026-10-01",
        start_time="10:00",
        end_time="11:30",
        duration_minutes=90,
        status="missed",
    )
    db_session.add(missed_session)
    db_session.commit()

    mock_client = _create_mock_gemini_client(
        tool_name="reschedule_missed_sessions_tool",
        tool_args={"reason": "Catch up on missed lecture"},
        final_explanation="I have found open time slots to reschedule your missed Database Systems session."
    )

    with patch.object(settings, "GEMINI_API_KEY", "mock-key"):
        with patch("app.services.gemini_service.get_gemini_client", return_value=mock_client):
            res = client.post("/api/v1/ai/agent/execute", json={"prompt": "Can you please reschedule my missed sessions?"})
            assert res.status_code == 200
            data = res.json()
            assert data["tool_name"] == "reschedule_missed_sessions_tool"
            assert data["action_type"] == "reschedule_missed"
            assert data["requires_approval"] is True
            assert len(data["proposed_sessions"]) >= 1
            assert "Makeup" in data["proposed_sessions"][0]["topic"]


def test_agent_optimize_schedule(client, db_session):
    # Seed active task to optimize
    task = Task(
        user_id=settings.DEMO_USER_ID,
        title="Algorithms Problem Set",
        subject="Algorithms",
        due_date="2026-10-15",
        priority="high",
        status="pending"
    )
    db_session.add(task)
    db_session.commit()

    mock_client = _create_mock_gemini_client(
        tool_name="optimize_study_schedule_tool",
        tool_args={"available_hours": 3.0, "preferences": "Balanced workload"},
        final_explanation="I optimized your study schedule to avoid burnout and target urgent assignments."
    )

    with patch.object(settings, "GEMINI_API_KEY", "mock-key"):
        with patch("app.services.gemini_service.get_gemini_client", return_value=mock_client):
            res = client.post("/api/v1/ai/agent/execute", json={"prompt": "Optimize my schedule for tomorrow"})
            assert res.status_code == 200
            data = res.json()
            assert data["tool_name"] == "optimize_study_schedule_tool"
            assert data["action_type"] == "optimize_schedule"
            assert data["requires_approval"] is True
            assert len(data["proposed_sessions"]) >= 1


def test_agent_optimize_schedule_empty_db(client, db_session):
    # Verifies Phase 5 empty database behavior: generates general recommendation without fabricating coursework
    mock_client = _create_mock_gemini_client(
        tool_name="optimize_study_schedule_tool",
        tool_args={"available_hours": 3.0, "preferences": "Balanced workload"},
        final_explanation="Here is a general daily schedule recommendation based on your requested 3.0 hours."
    )

    with patch.object(settings, "GEMINI_API_KEY", "mock-key"):
        with patch("app.services.gemini_service.get_gemini_client", return_value=mock_client):
            res = client.post("/api/v1/ai/agent/execute", json={"prompt": "Optimize my schedule for tomorrow"})
            assert res.status_code == 200
            data = res.json()
            assert data["tool_name"] == "optimize_study_schedule_tool"
            assert data["action_type"] == "optimize_schedule"
            assert data["is_general_recommendation"] is True
            assert data["requires_approval"] is True
            assert len(data["proposed_sessions"]) > 0
            assert any(s["event_type"] == "study" for s in data["proposed_sessions"])



def test_agent_academic_coaching_direct(client):
    # Gemini answers directly with coaching text (no tool call)
    mock_resp = MagicMock()
    mock_resp.function_calls = None
    mock_resp.text = "Alpha-beta pruning reduces the search space by evaluating minimax cutoffs."

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    with patch.object(settings, "GEMINI_API_KEY", "mock-key"):
        with patch("app.services.gemini_service.get_gemini_client", return_value=mock_client):
            res = client.post("/api/v1/ai/agent/execute", json={"prompt": "Explain alpha-beta pruning"})
            assert res.status_code == 200
            data = res.json()
            assert data["action_type"] == "academic_coaching"
            assert data["requires_approval"] is False
            assert "Alpha-beta pruning" in data["explanation"]


def test_safe_schedule_approval_persists_data(client, db_session):
    proposed = [
        {
            "subject": "Fundamentals of AI",
            "topic": "Game Tree Minimax",
            "date": "2026-10-25",
            "start_time": "14:00",
            "end_time": "15:30",
            "duration_minutes": 90,
            "reason": "Midterm preparation",
            "status": "upcoming",
            "color": "#C5A059",
        }
    ]

    res = client.post("/api/v1/ai/schedule/approve", json={"sessions": proposed})
    assert res.status_code == 200
    data = res.json()
    assert data["approved"] is True
    assert data["saved_count"] == 1
    assert len(data["saved_session_ids"]) == 1

    # Verify directly in SQLite
    saved_session = db_session.query(StudySession).filter(
        StudySession.id == data["saved_session_ids"][0]
    ).first()
    assert saved_session is not None
    assert saved_session.title == "Game Tree Minimax"
    assert saved_session.date == "2026-10-25"


def test_safe_schedule_rejection_leaves_database_unmodified(client, db_session):
    initial_count = db_session.query(StudySession).filter(
        StudySession.user_id == settings.DEMO_USER_ID
    ).count()

    res = client.post(
        "/api/v1/ai/schedule/reject",
        json={"reason": "Times do not suit my personal schedule"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["approved"] is False
    assert "rejected" in data["message"].lower()

    # Verify session count is strictly unchanged
    final_count = db_session.query(StudySession).filter(
        StudySession.user_id == settings.DEMO_USER_ID
    ).count()
    assert initial_count == final_count


def test_agent_activity_logs(client):
    mock_client = _create_mock_gemini_client(
        tool_name="query_study_progress_tool",
        tool_args={"query_focus": "tasks"},
        final_explanation="Progress query complete."
    )

    with patch.object(settings, "GEMINI_API_KEY", "mock-key"):
        with patch("app.services.gemini_service.get_gemini_client", return_value=mock_client):
            client.post("/api/v1/ai/agent/execute", json={"prompt": "Give me a summary of my study tasks"})

    # Fetch logs
    res = client.get("/api/v1/ai/logs")
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) >= 1
    assert "tool_name" in logs[0]
    assert "action_type" in logs[0]


def test_gemini_transient_error_fallback(client):
    """Verifies that transient 503 errors trigger fallback to secondary model."""
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.function_calls = None
    mock_resp.text = "Grounded advice from fallback model."

    # First call (gemini-3.5-flash-lite) raises 503; second call (gemini-3.5-flash) succeeds
    mock_client.models.generate_content.side_effect = [
        Exception("503 UNAVAILABLE. Model experiencing high demand."),
        mock_resp
    ]

    with patch.object(settings, "GEMINI_API_KEY", "mock-key"):
        with patch("app.services.gemini_service.get_gemini_client", return_value=mock_client):
            res = client.post("/api/v1/ai/agent/execute", json={"prompt": "Explain study strategies"})
            assert res.status_code == 200
            assert mock_client.models.generate_content.call_count == 2
            assert "fallback model" in res.json()["explanation"]


def test_gemini_non_transient_error_no_fallback(client):
    """Verifies that non-transient errors (e.g. 401 Unauthorized or 400 Invalid) do NOT fall back."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("401 UNAUTHORIZED. API_KEY_INVALID")

    with patch.object(settings, "GEMINI_API_KEY", "invalid-key"):
        with patch("app.services.gemini_service.get_gemini_client", return_value=mock_client):
            res = client.post("/api/v1/ai/agent/execute", json={"prompt": "Explain study strategies"})
            assert res.status_code == 401
            # Should have failed immediately without calling secondary model
            assert mock_client.models.generate_content.call_count == 1


def test_agent_preserves_thought_signatures_in_synthesis(client, db_session):
    """Verifies that candidate content (including thought signature) is passed to Round 2."""
    mock_fc = MagicMock()
    mock_fc.name = "query_study_progress_tool"
    mock_fc.args = {"query_focus": "tasks"}

    mock_candidate_content = MagicMock()
    mock_candidate_content.parts = ["thought_signature_part", "function_call_part"]
    mock_candidate = MagicMock()
    mock_candidate.content = mock_candidate_content

    mock_resp1 = MagicMock()
    mock_resp1.function_calls = [mock_fc]
    mock_resp1.candidates = [mock_candidate]

    mock_resp2 = MagicMock()
    mock_resp2.function_calls = None
    mock_resp2.text = "You are on track with your study tasks."

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = [mock_resp1, mock_resp2]

    with patch.object(settings, "GEMINI_API_KEY", "mock-key"):
        with patch("app.services.gemini_service.get_gemini_client", return_value=mock_client):
            res = client.post("/api/v1/ai/agent/execute", json={"prompt": "How am I doing on my coursework tasks?"})
            assert res.status_code == 200
            assert mock_client.models.generate_content.call_count == 2
            # Inspect args of second call to verify mock_candidate_content was included
            second_call_contents = mock_client.models.generate_content.call_args_list[1][1]["contents"]
            assert mock_candidate_content in second_call_contents
