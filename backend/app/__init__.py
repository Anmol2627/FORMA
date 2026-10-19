import logging
import os
from typing import Optional
from flask import Flask, jsonify
from backend.app.config import config_by_name
from backend.app.extensions import db, migrate, jwt, cors
from backend.app.utils.errors import register_error_handlers
from backend.app.routes import (
    health_bp,
    auth_bp,
    quizzes_bp,
    attempts_bp,
    ai_bp,
    documents_bp,
    chat_bp,
    progress_bp,
)


def configure_jwt_callbacks(jwt_manager):
    @jwt_manager.unauthorized_loader
    def custom_unauthorized_response(callback):
        return jsonify({
            "error": {
                "code": "unauthorized",
                "message": "Authorization header with Bearer token is required."
            }
        }), 401

    @jwt_manager.invalid_token_loader
    def custom_invalid_token_response(callback):
        return jsonify({
            "error": {
                "code": "invalid_token",
                "message": "The provided authentication token is invalid or malformed."
            }
        }), 401

    @jwt_manager.expired_token_loader
    def custom_expired_token_response(jwt_header, jwt_payload):
        return jsonify({
            "error": {
                "code": "token_expired",
                "message": "The authentication token has expired. Please log in again."
            }
        }), 401

    @jwt_manager.revoked_token_loader
    def custom_revoked_token_response(jwt_header, jwt_payload):
        return jsonify({
            "error": {
                "code": "token_revoked",
                "message": "The authentication token has been revoked."
            }
        }), 401


def create_app(config_name: Optional[str] = None) -> Flask:
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    config_cls = config_by_name.get(config_name, config_by_name["development"])
    app.config.from_object(config_cls)

    # Logging setup (avoid exposing secrets/tokens)
    logging.basicConfig(
        level=logging.DEBUG if app.config.get("DEBUG") else logging.INFO,
        format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )

    # Ensure uploads directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    configure_jwt_callbacks(jwt)
    cors.init_app(app, origins=app.config.get("CORS_ORIGINS", ["*"]), supports_credentials=True)

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints with /api/v1 prefix
    api_prefix = "/api/v1"
    app.register_blueprint(health_bp, url_prefix=api_prefix)
    app.register_blueprint(auth_bp, url_prefix=api_prefix)
    app.register_blueprint(quizzes_bp, url_prefix=api_prefix)
    app.register_blueprint(attempts_bp, url_prefix=api_prefix)
    app.register_blueprint(ai_bp, url_prefix=api_prefix)
    app.register_blueprint(documents_bp, url_prefix=api_prefix)
    app.register_blueprint(chat_bp, url_prefix=api_prefix)
    app.register_blueprint(progress_bp, url_prefix=api_prefix)

    return app
