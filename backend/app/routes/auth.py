from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app.schemas.auth import RegisterRequest, LoginRequest
from backend.app.services.auth_service import AuthService
from backend.app.utils.validators import validate_payload

auth_bp = Blueprint("auth", __name__)
auth_service = AuthService()


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    data = validate_payload(RegisterRequest)
    result = auth_service.register(data)
    return jsonify(result), 201


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = validate_payload(LoginRequest)
    result = auth_service.login(data)
    return jsonify(result), 200


@auth_bp.route("/auth/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    profile = auth_service.get_current_user_profile(user_id)
    return jsonify({"user": profile}), 200
