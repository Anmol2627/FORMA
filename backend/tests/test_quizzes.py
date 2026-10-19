def create_sample_quiz_payload(title="Biology 101", visibility="private"):
    return {
        "title": title,
        "description": "Introductory Quiz",
        "visibility": visibility,
        "questions": [
            {
                "prompt": "What organelle is known as the powerhouse of the cell?",
                "explanation": "Mitochondria produce ATP through cellular respiration.",
                "display_position": 0,
                "topic": "Cell Biology",
                "difficulty": "easy",
                "options": [
                    {"option_text": "Mitochondria", "is_correct": True},
                    {"option_text": "Ribosome", "is_correct": False},
                    {"option_text": "Nucleus", "is_correct": False},
                    {"option_text": "Endoplasmic Reticulum", "is_correct": False}
                ]
            },
            {
                "prompt": "Which base is found in RNA but not DNA?",
                "explanation": "Uracil replaces Thymine in RNA.",
                "display_position": 1,
                "topic": "Genetics",
                "difficulty": "medium",
                "options": [
                    {"option_text": "Thymine", "is_correct": False},
                    {"option_text": "Uracil", "is_correct": True},
                    {"option_text": "Guanine", "is_correct": False},
                    {"option_text": "Cytosine", "is_correct": False}
                ]
            }
        ]
    }


def test_create_quiz_success(client, auth_headers):
    payload = create_sample_quiz_payload()
    res = client.post("/api/v1/quizzes", json=payload, headers=auth_headers)
    assert res.status_code == 201
    quiz = res.get_json()["quiz"]
    assert quiz["title"] == "Biology 101"
    assert quiz["visibility"] == "private"
    assert len(quiz["questions"]) == 2
    assert len(quiz["questions"][0]["options"]) == 4


def test_create_quiz_validation_rules(client, auth_headers):
    # Blank title
    payload = create_sample_quiz_payload(title="   ")
    res = client.post("/api/v1/quizzes", json=payload, headers=auth_headers)
    assert res.status_code == 422

    # Question with zero correct options
    payload_zero_correct = create_sample_quiz_payload()
    payload_zero_correct["questions"][0]["options"][0]["is_correct"] = False
    res2 = client.post("/api/v1/quizzes", json=payload_zero_correct, headers=auth_headers)
    assert res2.status_code == 422

    # Question with multiple correct options
    payload_multi_correct = create_sample_quiz_payload()
    payload_multi_correct["questions"][0]["options"][1]["is_correct"] = True
    res3 = client.post("/api/v1/quizzes", json=payload_multi_correct, headers=auth_headers)
    assert res3.status_code == 422


def test_list_and_get_quizzes_ownership(client, auth_headers, other_user_headers):
    # User 1 creates private quiz
    res1 = client.post("/api/v1/quizzes", json=create_sample_quiz_payload("Private Quiz 1", "private"), headers=auth_headers)
    quiz1_id = res1.get_json()["quiz"]["id"]

    # User 1 creates public quiz
    res2 = client.post("/api/v1/quizzes", json=create_sample_quiz_payload("Public Quiz 1", "public"), headers=auth_headers)
    quiz2_id = res2.get_json()["quiz"]["id"]

    # User 2 lists quizzes
    list_res = client.get("/api/v1/quizzes", headers=other_user_headers)
    assert list_res.status_code == 200
    quizzes = list_res.get_json()["quizzes"]
    quiz_ids = [q["id"] for q in quizzes]
    assert quiz2_id in quiz_ids
    assert quiz1_id not in quiz_ids  # Private quiz of user 1 must NOT appear

    # User 2 tries to GET private quiz directly -> 403 Forbidden
    get_res = client.get(f"/api/v1/quizzes/{quiz1_id}", headers=other_user_headers)
    assert get_res.status_code == 403
    assert get_res.get_json()["error"]["code"] == "forbidden_quiz_access"

    # User 2 tries to GET public quiz directly -> 200 OK
    get_res2 = client.get(f"/api/v1/quizzes/{quiz2_id}", headers=other_user_headers)
    assert get_res2.status_code == 200


def test_update_quiz_and_ownership(client, auth_headers, other_user_headers):
    res = client.post("/api/v1/quizzes", json=create_sample_quiz_payload(), headers=auth_headers)
    quiz_id = res.get_json()["quiz"]["id"]

    # Other user attempts to update -> 403 Forbidden
    res_forbidden = client.patch(f"/api/v1/quizzes/{quiz_id}", json={"title": "Hacked Title"}, headers=other_user_headers)
    assert res_forbidden.status_code == 403

    # Owner updates title and description -> 200 OK
    res_ok = client.patch(f"/api/v1/quizzes/{quiz_id}", json={"title": "Updated Biology 101"}, headers=auth_headers)
    assert res_ok.status_code == 200
    assert res_ok.get_json()["quiz"]["title"] == "Updated Biology 101"


def test_delete_quiz_and_ownership(client, auth_headers, other_user_headers):
    res = client.post("/api/v1/quizzes", json=create_sample_quiz_payload(), headers=auth_headers)
    quiz_id = res.get_json()["quiz"]["id"]

    # Other user attempts to delete -> 403 Forbidden
    res_forbidden = client.delete(f"/api/v1/quizzes/{quiz_id}", headers=other_user_headers)
    assert res_forbidden.status_code == 403

    # Owner deletes -> 200 OK
    res_ok = client.delete(f"/api/v1/quizzes/{quiz_id}", headers=auth_headers)
    assert res_ok.status_code == 200

    # Ensure deleted
    res_get = client.get(f"/api/v1/quizzes/{quiz_id}", headers=auth_headers)
    assert res_get.status_code == 404
