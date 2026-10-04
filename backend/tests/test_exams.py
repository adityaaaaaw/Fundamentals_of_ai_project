def test_exam_lifecycle(client):
    payload = {
        "title": "AI Midterm",
        "subject": "Fundamentals of AI",
        "exam_date": "2026-10-20",
        "exam_time": "10:00 AM - 12:00 PM",
        "room": "Room 101",
        "weight": "30%",
    }
    res = client.post("/api/v1/exams", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "AI Midterm"
    exam_id = data["id"]

    # Read all exams
    list_res = client.get("/api/v1/exams")
    assert list_res.status_code == 200
    exams = list_res.json()
    assert len(exams) >= 1
    assert "days_remaining" in exams[0]

    # Update exam
    put_res = client.put(f"/api/v1/exams/{exam_id}", json={"room": "Hall C"})
    assert put_res.status_code == 200
    assert put_res.json()["room"] == "Hall C"

    # Delete exam
    del_res = client.delete(f"/api/v1/exams/{exam_id}")
    assert del_res.status_code == 204
