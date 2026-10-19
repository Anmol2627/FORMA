from backend.tests.test_quizzes import create_sample_quiz_payload


def test_take_quiz_never_leaks_answer_keys(client, auth_headers):
    # Create a quiz
    res = client.post("/api/v1/quizzes", json=create_sample_quiz_payload(), headers=auth_headers)
    quiz_id = res.get_json()["quiz"]["id"]

    # Take endpoint
    take_res = client.get(f"/api/v1/quizzes/{quiz_id}/take", headers=auth_headers)
    assert take_res.status_code == 200
    take_data = take_res.get_json()["quiz"]

    # Assertions on questions
    assert len(take_data["questions"]) == 2
    for q in take_data["questions"]:
        assert "explanation" not in q
        assert "is_correct" not in q
        for opt in q["options"]:
            assert "is_correct" not in opt
            assert "id" in opt
            assert "option_text" in opt


def test_submit_attempt_scoring_and_review(client, auth_headers, other_user_headers):
    # Setup quiz
    create_res = client.post("/api/v1/quizzes", json=create_sample_quiz_payload(), headers=auth_headers)
    quiz = create_res.get_json()["quiz"]
    quiz_id = quiz["id"]

    q1 = quiz["questions"][0]
    q2 = quiz["questions"][1]

    # Find correct and incorrect option IDs
    q1_correct_opt = next(o["id"] for o in q1["options"] if o["is_correct"])
    q2_incorrect_opt = next(o["id"] for o in q2["options"] if not o["is_correct"])

    # Submit attempt: 1 correct, 1 incorrect
    submission_payload = {
        "answers": [
            {"question_id": q1["id"], "selected_option_id": q1_correct_opt},
            {"question_id": q2["id"], "selected_option_id": q2_incorrect_opt}
        ]
    }
    submit_res = client.post(f"/api/v1/quizzes/{quiz_id}/attempts", json=submission_payload, headers=auth_headers)
    assert submit_res.status_code == 201
    summary = submit_res.get_json()["attempt"]
    assert summary["score"] == 1
    assert summary["total_questions"] == 2
    assert summary["accuracy_percentage"] == 50.0

    attempt_id = summary["id"]

    # View results as attempt owner
    results_res = client.get(f"/api/v1/attempts/{attempt_id}/results", headers=auth_headers)
    assert results_res.status_code == 200
    results_data = results_res.get_json()["attempt"]
    assert len(results_data["answers"]) == 2
    assert results_data["answers"][0]["is_correct"] is True
    assert results_data["answers"][1]["is_correct"] is False
    assert results_data["answers"][0]["explanation"] is not None

    # Other user attempts to view results -> 403 Forbidden
    forbidden_res = client.get(f"/api/v1/attempts/{attempt_id}/results", headers=other_user_headers)
    assert forbidden_res.status_code == 403
    assert forbidden_res.get_json()["error"]["code"] == "forbidden_attempt_access"


def test_submit_attempt_unanswered_questions(client, auth_headers):
    create_res = client.post("/api/v1/quizzes", json=create_sample_quiz_payload(), headers=auth_headers)
    quiz = create_res.get_json()["quiz"]
    quiz_id = quiz["id"]
    q1 = quiz["questions"][0]
    q1_correct_opt = next(o["id"] for o in q1["options"] if o["is_correct"])

    # Submit only 1 answer (leaving 1 question unanswered)
    submission_payload = {
        "answers": [
            {"question_id": q1["id"], "selected_option_id": q1_correct_opt}
        ]
    }
    submit_res = client.post(f"/api/v1/quizzes/{quiz_id}/attempts", json=submission_payload, headers=auth_headers)
    assert submit_res.status_code == 201
    summary = submit_res.get_json()["attempt"]
    assert summary["score"] == 1
    assert summary["total_questions"] == 2
    assert summary["accuracy_percentage"] == 50.0


def test_submit_attempt_rejects_duplicates_and_invalid_references(client, auth_headers):
    create_res = client.post("/api/v1/quizzes", json=create_sample_quiz_payload(), headers=auth_headers)
    quiz = create_res.get_json()["quiz"]
    quiz_id = quiz["id"]
    q1 = quiz["questions"][0]

    # Duplicate answer for same question
    dup_payload = {
        "answers": [
            {"question_id": q1["id"], "selected_option_id": q1["options"][0]["id"]},
            {"question_id": q1["id"], "selected_option_id": q1["options"][1]["id"]}
        ]
    }
    res_dup = client.post(f"/api/v1/quizzes/{quiz_id}/attempts", json=dup_payload, headers=auth_headers)
    assert res_dup.status_code == 422

    # Invalid question reference
    invalid_q_payload = {
        "answers": [
            {"question_id": "non-existent-question-id", "selected_option_id": None}
        ]
    }
    res_inv_q = client.post(f"/api/v1/quizzes/{quiz_id}/attempts", json=invalid_q_payload, headers=auth_headers)
    assert res_inv_q.status_code == 400
    assert res_inv_q.get_json()["error"]["code"] == "invalid_question_reference"

    # Invalid option reference
    invalid_opt_payload = {
        "answers": [
            {"question_id": q1["id"], "selected_option_id": "fake-opt-id"}
        ]
    }
    res_inv_opt = client.post(f"/api/v1/quizzes/{quiz_id}/attempts", json=invalid_opt_payload, headers=auth_headers)
    assert res_inv_opt.status_code == 400
    assert res_inv_opt.get_json()["error"]["code"] == "invalid_option_reference"
