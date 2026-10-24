from backend.tests.test_quizzes import create_sample_quiz_payload


def test_progress_empty_state(client, auth_headers):
    res = client.get("/api/v1/progress", headers=auth_headers)
    assert res.status_code == 200
    progress = res.get_json()["progress"]
    assert progress["total_attempts"] == 0
    assert progress["total_questions_answered"] == 0
    assert progress["total_correct_answers"] == 0
    assert progress["overall_accuracy_percentage"] == 0.0
    assert progress["recent_attempts"] == []


def test_progress_multiple_attempts_and_accuracy(client, auth_headers, other_user_headers):
    # Setup quiz
    res_quiz = client.post("/api/v1/quizzes", json=create_sample_quiz_payload(), headers=auth_headers)
    quiz = res_quiz.get_json()["quiz"]
    quiz_id = quiz["id"]
    q1 = quiz["questions"][0]
    q2 = quiz["questions"][1]
    q1_correct = next(o["id"] for o in q1["options"] if o["is_correct"])
    q2_correct = next(o["id"] for o in q2["options"] if o["is_correct"])
    q2_incorrect = next(o["id"] for o in q2["options"] if not o["is_correct"])

    # Attempt 1: 2 correct (2/2 = 100%)
    client.post(
        f"/api/v1/quizzes/{quiz_id}/attempts",
        json={"answers": [{"question_id": q1["id"], "selected_option_id": q1_correct}, {"question_id": q2["id"], "selected_option_id": q2_correct}]},
        headers=auth_headers
    )

    # Attempt 2: 1 correct (1/2 = 50%)
    client.post(
        f"/api/v1/quizzes/{quiz_id}/attempts",
        json={"answers": [{"question_id": q1["id"], "selected_option_id": q1_correct}, {"question_id": q2["id"], "selected_option_id": q2_incorrect}]},
        headers=auth_headers
    )

    # Primary user progress
    res_prog = client.get("/api/v1/progress", headers=auth_headers)
    assert res_prog.status_code == 200
    p = res_prog.get_json()["progress"]
    assert p["total_attempts"] == 2
    assert p["total_questions_answered"] == 4
    assert p["total_correct_answers"] == 3
    assert p["overall_accuracy_percentage"] == 75.0
    assert len(p["recent_attempts"]) == 2

    # Secondary user progress isolation check: must still be 0
    res_other = client.get("/api/v1/progress", headers=other_user_headers)
    assert res_other.status_code == 200
    p_other = res_other.get_json()["progress"]
    assert p_other["total_attempts"] == 0
    assert p_other["total_questions_answered"] == 0
