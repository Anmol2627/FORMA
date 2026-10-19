from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app.schemas.ai import QuizGenerateRequest
from backend.app.schemas.quiz import QuizCreateSchema, QuestionCreateSchema, OptionCreateSchema
from backend.app.ai.llm_client import get_llm_client_from_config
from backend.app.ai.quiz_generator import AIQuizGenerator
from backend.app.services.quiz_service import QuizService
from backend.app.utils.validators import validate_payload

ai_bp = Blueprint("ai", __name__)
quiz_service = QuizService()


@ai_bp.route("/ai/generate-quiz", methods=["POST"])
@jwt_required()
def generate_quiz():
    user_id = get_jwt_identity()
    req_data = validate_payload(QuizGenerateRequest)

    # Use client configured from application configuration (or mock injected in test mode)
    llm_client = getattr(current_app, "llm_client", None)
    if not llm_client:
        llm_client = get_llm_client_from_config(current_app.config)

    generator = AIQuizGenerator(llm_client=llm_client)
    generated_payload = generator.generate_quiz(req_data)

    # Convert generated payload to QuizCreateSchema and save as private quiz owned by the user
    question_schemas = []
    for idx, q in enumerate(generated_payload.questions):
        option_schemas = [
            OptionCreateSchema(option_text=opt.option_text, is_correct=opt.is_correct)
            for opt in q.options
        ]
        q_schema = QuestionCreateSchema(
            prompt=q.prompt,
            explanation=q.explanation,
            display_position=idx,
            topic=req_data.topic,
            difficulty=q.difficulty or req_data.difficulty,
            options=option_schemas
        )
        question_schemas.append(q_schema)

    quiz_schema = QuizCreateSchema(
        title=generated_payload.title or f"AI Quiz: {req_data.topic}",
        description=generated_payload.description or f"Generated quiz on '{req_data.topic}' ({req_data.difficulty} difficulty).",
        visibility="private",
        generation_metadata={
            "generated_by": "ai",
            "topic": req_data.topic,
            "difficulty": req_data.difficulty,
            "question_count": req_data.question_count,
            "disclaimer": "AI-generated questions may require human review."
        },
        questions=question_schemas
    )

    saved_quiz = quiz_service.create_quiz(user_id=user_id, schema=quiz_schema)
    return jsonify({
        "message": "AI quiz generated and saved successfully.",
        "quiz": saved_quiz
    }), 201
