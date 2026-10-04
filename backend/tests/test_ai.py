from unittest.mock import MagicMock, patch
from app.core.config import settings


def test_ai_missing_key_returns_503(client):
    # Ensure key is empty
    with patch.object(settings, "GEMINI_API_KEY", ""):
        res = client.post("/api/v1/ai/generate-plan", json={"goal": "Prepare for finals"})
        assert res.status_code == 503
        assert "not configured" in res.json()["detail"].lower()


def test_ai_generate_plan_mocked_success(client):
    mock_plan_json = """
    {
      "goal": "Prepare for finals",
      "summary": "High-yield active recall revision schedule",
      "total_hours": 3.0,
      "blocks": [
        {
          "time": "09:00 - 10:30",
          "start_time": "09:00",
          "end_time": "10:30",
          "subject": "Fundamentals of AI",
          "topic": "Search Algorithms Review",
          "duration_minutes": 90,
          "strategy": "Solve 2 heuristic search problems",
          "break_recommendation": "10m break",
          "priority": "high"
        }
      ]
    }
    """
    mock_response = MagicMock()
    mock_response.text = mock_plan_json

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(settings, "GEMINI_API_KEY", "mock-test-key"):
        with patch("app.services.gemini_service.get_gemini_client", return_value=mock_client):
            res = client.post("/api/v1/ai/generate-plan", json={"goal": "Prepare for finals"})
            assert res.status_code == 200
            data = res.json()
            assert data["goal"] == "Prepare for finals"
            assert len(data["blocks"]) == 1
            assert data["blocks"][0]["subject"] == "Fundamentals of AI"


def test_ai_ask_mocked_success(client):
    mock_ask_json = """
    {
      "answer": "Active recall is the most effective study method for AI theory.",
      "suggested_actions": ["Self-test without looking at notes", "Diagram minimax game trees"]
    }
    """
    mock_response = MagicMock()
    mock_response.text = mock_ask_json
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(settings, "GEMINI_API_KEY", "mock-test-key"):
        with patch("app.services.gemini_service.get_gemini_client", return_value=mock_client):
            res = client.post("/api/v1/ai/ask", json={"question": "How should I study for AI?"})
            assert res.status_code == 200
            data = res.json()
            assert "Active recall" in data["answer"]
            assert len(data["suggested_actions"]) == 2


def test_ai_malformed_json_returns_502(client):
    mock_response = MagicMock()
    mock_response.text = "This is not valid json content!"
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(settings, "GEMINI_API_KEY", "mock-test-key"):
        with patch("app.services.gemini_service.get_gemini_client", return_value=mock_client):
            res = client.post("/api/v1/ai/generate-plan", json={"goal": "Prepare for finals"})
            assert res.status_code == 502
            assert "malformed" in res.json()["detail"].lower()
