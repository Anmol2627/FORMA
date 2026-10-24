from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app.services.attempt_service import AttemptService

attempts_bp = Blueprint("attempts", __name__)
attempt_service = AttemptService()


@attempts_bp.route("/attempts/<attempt_id>/results", methods=["GET"])
@jwt_required()
def get_attempt_results(attempt_id: str):
    """
    Returns full attempt review (including user selections, correct answers, and explanations)
    exclusively to the user who took the attempt.
    """
    user_id = get_jwt_identity()
    results = attempt_service.get_attempt_results(attempt_id=attempt_id, user_id=user_id)
    return jsonify({"attempt": results}), 200
