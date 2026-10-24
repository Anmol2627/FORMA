import json
import pytest
from backend.app.ai.llm_client import MockLLMClient, LLMError, OpenAILLMClient, LLMConfigurationError
from backend.app.schemas.ai import QuizGenerateRequest
from backend.app.ai.quiz_generator import AIQuizGenerator


def test_ai_quiz_generation_valid(client, app, auth_headers):
    # Set mock valid response
    valid_mock = json.dumps({
        "title": "Quantum Physics Quiz",
        "description": "Test your fundamentals of quantum mechanics",
        "questions": [
            {
                "prompt": "What is Planck's constant approximately?",
                "explanation": "Planck's constant is approximately 6.626 x 10^-34 J s.",
                "difficulty": "medium",
                "options": [
                    {"option_text": "6.626 x 10^-34 J s", "is_correct": True},
                    {"option_text": "3.00 x 10^8 m/s", "is_correct": False},
                    {"option_text": "9.8 m/s^2", "is_correct": False},
                    {"option_text": "1.602 x 10^-19 C", "is_correct": False}
                ]
            }
        ]
    })
    app.llm_client = MockLLMClient(mock_response=valid_mock)

    req_payload = {
        "topic": "Quantum Mechanics",
        "question_count": 1,
        "difficulty": "medium"
    }
    res = client.post("/api/v1/ai/generate-quiz", json=req_payload, headers=auth_headers)
    assert res.status_code == 201
    data = res.get_json()
    assert "quiz" in data
    quiz = data["quiz"]
    assert quiz["title"] == "Quantum Physics Quiz"
    assert quiz["visibility"] == "private"
    assert len(quiz["questions"]) == 1
    assert quiz["questions"][0]["options"][0]["is_correct"] is True


def test_ai_quiz_generation_malformed_json(app):
    generator = AIQuizGenerator(llm_client=MockLLMClient(mock_response="Not valid JSON response"))
    req = QuizGenerateRequest(topic="Biology", question_count=1)

    with pytest.raises(LLMError) as exc_info:
        generator.generate_quiz(req)
    assert exc_info.value.code == "llm_malformed_response"


def test_ai_quiz_generation_invalid_question_structure(app):
    # Invalid structure: two correct options
    bad_structure_mock = json.dumps({
        "title": "Broken Quiz",
        "questions": [
            {
                "prompt": "What is 2+2?",
                "options": [
                    {"option_text": "4", "is_correct": True},
                    {"option_text": "Four", "is_correct": True}  # Multiple correct!
                ]
            }
        ]
    })
    generator = AIQuizGenerator(llm_client=MockLLMClient(mock_response=bad_structure_mock))
    req = QuizGenerateRequest(topic="Math", question_count=1)

    with pytest.raises(LLMError) as exc_info:
        generator.generate_quiz(req)
    assert exc_info.value.code == "llm_invalid_structure"


def test_ai_client_missing_configuration():
    client = OpenAILLMClient(api_key="")
    with pytest.raises(LLMConfigurationError):
        client.generate_chat_completion(messages=[{"role": "user", "content": "hi"}])
