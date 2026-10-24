from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app.schemas.chat import ChatSessionCreateRequest, ChatMessageSendRequest
from backend.app.services.chat_service import ChatService
from backend.app.utils.validators import validate_payload

chat_bp = Blueprint("chat", __name__)


def _get_chat_service() -> ChatService:
    """Construct ChatService with the RAG service attached to current app."""
    rag_service = getattr(current_app, "rag_service", None)
    return ChatService(rag_service=rag_service)


@chat_bp.route("/chat/sessions", methods=["POST"])
@jwt_required()
def create_session():
    user_id = get_jwt_identity()
    data = validate_payload(ChatSessionCreateRequest)
    session = _get_chat_service().create_session(
        user_id=user_id,
        document_id=data.document_id,
        title=data.title
    )
    return jsonify({"session": session}), 201


@chat_bp.route("/chat/sessions", methods=["GET"])
@jwt_required()
def list_sessions():
    user_id = get_jwt_identity()
    sessions = _get_chat_service().list_sessions(user_id=user_id)
    return jsonify({"sessions": sessions}), 200


@chat_bp.route("/chat/sessions/<session_id>/messages", methods=["GET"])
@jwt_required()
def get_messages(session_id: str):
    user_id = get_jwt_identity()
    messages = _get_chat_service().get_session_messages(session_id=session_id, user_id=user_id)
    return jsonify({"messages": messages}), 200


@chat_bp.route("/chat/sessions/<session_id>/messages", methods=["POST"])
@jwt_required()
def send_message(session_id: str):
    """
    Receives a user message, retrieves relevant PDF context (TF-IDF),
    and calls the LLM to generate a grounded response with page citations.
    """
    user_id = get_jwt_identity()
    data = validate_payload(ChatMessageSendRequest)
    result = _get_chat_service().send_message(
        session_id=session_id,
        user_id=user_id,
        content=data.content
    )
    return jsonify(result), 200

