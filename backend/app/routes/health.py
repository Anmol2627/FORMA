from flask import Blueprint, jsonify
from sqlalchemy import text
from backend.app.extensions import db
from backend.app.utils.errors import AppError

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "FORMA Backend API",
        "version": "1.0.0"
    }), 200


@health_bp.route("/health/ready", methods=["GET"])
def readiness_check():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({
            "status": "ready",
            "database": "connected"
        }), 200
    except Exception as e:
        raise AppError(
            message=f"Database connectivity check failed: {str(e)}",
            code="database_unavailable",
            status_code=503
        )
