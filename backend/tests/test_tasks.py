def test_create_and_get_tasks(client):
    # 1. Create a task
    payload = {
        "title": "Study A* Heuristics",
        "subject": "Fundamentals of AI",
        "due_date": "2026-10-10",
        "priority": "high",
        "status": "pending",
        "notes": "Chapter 3 review"
    }
    response = client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["title"] == "Study A* Heuristics"
    assert created["priority"] == "high"
    assert created["status"] == "pending"
    task_id = created["id"]

    # 2. Get by ID
    get_res = client.get(f"/api/v1/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == task_id

    # 3. Filter by subject
    list_res = client.get("/api/v1/tasks?subject=Fundamentals of AI")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 4. Search query
    search_res = client.get("/api/v1/tasks?search=Heuristics")
    assert search_res.status_code == 200
    assert len(search_res.json()) >= 1

    # 5. Patch status to completed
    patch_res = client.patch(f"/api/v1/tasks/{task_id}/status", json={"status": "completed"})
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "completed"

    # 6. Update task
    put_res = client.put(f"/api/v1/tasks/{task_id}", json={"title": "Updated A* Heuristics", "priority": "medium"})
    assert put_res.status_code == 200
    assert put_res.json()["title"] == "Updated A* Heuristics"
    assert put_res.json()["priority"] == "medium"

    # 7. Delete task
    del_res = client.delete(f"/api/v1/tasks/{task_id}")
    assert del_res.status_code == 204

    # 8. Verify 404 after delete
    get_deleted = client.get(f"/api/v1/tasks/{task_id}")
    assert get_deleted.status_code == 404
