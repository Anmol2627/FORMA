from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app.services.progress_service import ProgressService

progress_bp = Blueprint("progress", __name__)
progress_service = ProgressService()


@progress_bp.route("/progress", methods=["GET"])
@jwt_required()
def get_progress():
    user_id = get_jwt_identity()
    stats = progress_service.get_user_progress(user_id=user_id)
    return jsonify({"progress": stats}), 200
