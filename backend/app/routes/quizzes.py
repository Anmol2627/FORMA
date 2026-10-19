from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app.schemas.quiz import QuizCreateSchema, QuizUpdateSchema
from backend.app.schemas.attempt import AttemptSubmitSchema
from backend.app.services.quiz_service import QuizService
from backend.app.services.attempt_service import AttemptService
from backend.app.utils.validators import validate_payload

quizzes_bp = Blueprint("quizzes", __name__)
quiz_service = QuizService()
attempt_service = AttemptService()


@quizzes_bp.route("/quizzes", methods=["GET"])
@jwt_required()
def list_quizzes():
    user_id = get_jwt_identity()
    include_public_arg = request.args.get("include_public", "true").lower()
    include_public = include_public_arg not in ["false", "0", "no"]
    quizzes = quiz_service.list_quizzes(user_id=user_id, include_public=include_public)
    return jsonify({"quizzes": quizzes}), 200


@quizzes_bp.route("/quizzes", methods=["POST"])
@jwt_required()
def create_quiz():
    user_id = get_jwt_identity()
    data = validate_payload(QuizCreateSchema)
    quiz = quiz_service.create_quiz(user_id=user_id, schema=data)
    return jsonify({"quiz": quiz}), 201


@quizzes_bp.route("/quizzes/<quiz_id>", methods=["GET"])
@jwt_required()
def get_quiz(quiz_id: str):
    user_id = get_jwt_identity()
    quiz = quiz_service.get_quiz_by_id(quiz_id=quiz_id, current_user_id=user_id)
    return jsonify({"quiz": quiz}), 200


@quizzes_bp.route("/quizzes/<quiz_id>", methods=["PATCH"])
@jwt_required()
def update_quiz(quiz_id: str):
    user_id = get_jwt_identity()
    data = validate_payload(QuizUpdateSchema)
    updated = quiz_service.update_quiz(quiz_id=quiz_id, user_id=user_id, schema=data)
    return jsonify({"quiz": updated}), 200


@quizzes_bp.route("/quizzes/<quiz_id>", methods=["DELETE"])
@jwt_required()
def delete_quiz(quiz_id: str):
    user_id = get_jwt_identity()
    quiz_service.delete_quiz(quiz_id=quiz_id, user_id=user_id)
    return jsonify({"message": "Quiz deleted successfully."}), 200


@quizzes_bp.route("/quizzes/<quiz_id>/take", methods=["GET"])
@jwt_required()
def take_quiz(quiz_id: str):
    """
    Critical security boundary: Returns quiz questions and options with NO answer keys,
    correctness flags, or explanations.
    """
    user_id = get_jwt_identity()
    quiz_take_view = quiz_service.get_quiz_for_taking(quiz_id=quiz_id, current_user_id=user_id)
    return jsonify({"quiz": quiz_take_view}), 200


@quizzes_bp.route("/quizzes/<quiz_id>/attempts", methods=["POST"])
@jwt_required()
def submit_attempt(quiz_id: str):
    user_id = get_jwt_identity()
    data = validate_payload(AttemptSubmitSchema)
    result = attempt_service.submit_attempt(quiz_id=quiz_id, user_id=user_id, submission=data)
    return jsonify({"attempt": result}), 201
