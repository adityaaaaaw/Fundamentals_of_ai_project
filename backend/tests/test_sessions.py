def test_session_lifecycle_and_overlap_rules(client):
    # 1. Create initial session: 10:00 to 11:30
    payload_1 = {
        "title": "Minimax Algorithm",
        "subject": "Fundamentals of AI",
        "date": "2026-10-15",
        "start_time": "10:00",
        "end_time": "11:30",
        "status": "upcoming",
    }
    res_1 = client.post("/api/v1/sessions", json=payload_1)
    assert res_1.status_code == 201
    session_1 = res_1.json()
    assert session_1["duration_minutes"] == 90
    assert session_1["day_of_week"] == "Thursday"
    session_1_id = session_1["id"]

    # 2. Try overlapping session: 11:00 to 12:30 on same date -> 409 Conflict
    payload_overlap = {
        "title": "Alpha-Beta Pruning",
        "subject": "Fundamentals of AI",
        "date": "2026-10-15",
        "start_time": "11:00",
        "end_time": "12:30",
    }
    res_overlap = client.post("/api/v1/sessions", json=payload_overlap)
    assert res_overlap.status_code == 409
    assert "conflict" in res_overlap.json()["detail"].lower()

    # 3. Adjacent session: 11:30 to 13:00 on same date -> Allowed (201)
    payload_adjacent = {
        "title": "Matrix Diagonalization",
        "subject": "Linear Algebra",
        "date": "2026-10-15",
        "start_time": "11:30",
        "end_time": "13:00",
    }
    res_adjacent = client.post("/api/v1/sessions", json=payload_adjacent)
    assert res_adjacent.status_code == 201

    # 4. Update session 1 topic without changing times -> Should succeed (no false self-conflict)
    update_res = client.put(f"/api/v1/sessions/{session_1_id}", json={"title": "Updated Minimax Algorithm"})
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Minimax Algorithm"

    # 5. Patch status to completed
    patch_res = client.patch(f"/api/v1/sessions/{session_1_id}/status", json={"status": "completed"})
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "completed"

    # 6. Delete session
    del_res = client.delete(f"/api/v1/sessions/{session_1_id}")
    assert del_res.status_code == 204
