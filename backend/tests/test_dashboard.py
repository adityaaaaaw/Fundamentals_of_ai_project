def test_dashboard_calculations(client):
    # Create 1 completed task and 1 pending task
    client.post("/api/v1/tasks", json={
        "title": "Task 1", "subject": "CS", "due_date": "2026-10-10", "priority": "high", "status": "completed"
    })
    client.post("/api/v1/tasks", json={
        "title": "Task 2", "subject": "Math", "due_date": "2026-10-11", "priority": "high", "status": "pending"
    })

    # Summary
    res = client.get("/api/v1/dashboard/summary")
    assert res.status_code == 200
    summary = res.json()
    assert summary["total_tasks"] == 2
    assert summary["completed_tasks"] == 1
    assert summary["pending_tasks"] == 1
    assert summary["completion_rate"] == 50

    # Weekly progress
    res_prog = client.get("/api/v1/dashboard/weekly-progress")
    assert res_prog.status_code == 200
    prog = res_prog.json()
    assert "metrics" in prog
    assert len(prog["metrics"]) == 7

    # High priority tasks
    res_high = client.get("/api/v1/dashboard/high-priority-tasks")
    assert res_high.status_code == 200
    high_tasks = res_high.json()
    assert len(high_tasks) >= 1
    assert high_tasks[0]["status"] == "pending"


def test_dashboard_empty_initial_state(client):
    """Verifies that an empty database returns 0 metrics, 0 hours, and 0 streak with no crashes."""
    res = client.get("/api/v1/dashboard/summary")
    assert res.status_code == 200
    summary = res.json()
    assert summary["total_tasks"] == 0
    assert summary["completed_tasks"] == 0
    assert summary["pending_tasks"] == 0
    assert summary["completion_rate"] == 0
    assert summary["current_streak_days"] == 0
    assert summary["completed_study_time_minutes"] == 0

    res_prog = client.get("/api/v1/dashboard/weekly-progress")
    assert res_prog.status_code == 200
    prog = res_prog.json()
    assert "metrics" in prog
    assert len(prog["metrics"]) == 7
    for day_metric in prog["metrics"]:
        assert day_metric["studiedHours"] == 0.0
    assert prog["total_studied_hours"] == 0.0
    assert prog["current_streak_days"] == 0

    res_high = client.get("/api/v1/dashboard/high-priority-tasks")
    assert res_high.status_code == 200
    assert len(res_high.json()) == 0
