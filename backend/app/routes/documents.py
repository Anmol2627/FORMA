from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app.services.document_service import DocumentService
from backend.app.utils.errors import BadRequestError

documents_bp = Blueprint("documents", __name__)


def get_document_service() -> DocumentService:
    return DocumentService(
        upload_folder=current_app.config["UPLOAD_FOLDER"],
        max_content_length=current_app.config["MAX_CONTENT_LENGTH"]
    )


@documents_bp.route("/documents", methods=["POST"])
@jwt_required()
def upload_document():
    user_id = get_jwt_identity()
    if "file" not in request.files:
        raise BadRequestError("Multipart form must include 'file' field.", code="missing_file_field")

    uploaded_file = request.files["file"]
    service = get_document_service()
    doc_data = service.upload_and_process_pdf(user_id=user_id, file=uploaded_file)
    return jsonify({
        "message": "Document uploaded and processed successfully.",
        "document": doc_data
    }), 201


@documents_bp.route("/documents", methods=["GET"])
@jwt_required()
def list_documents():
    user_id = get_jwt_identity()
    service = get_document_service()
    docs = service.list_documents(user_id=user_id)
    return jsonify({"documents": docs}), 200


@documents_bp.route("/documents/<document_id>", methods=["GET"])
@jwt_required()
def get_document(document_id: str):
    user_id = get_jwt_identity()
    service = get_document_service()
    doc = service.get_document(document_id=document_id, user_id=user_id)
    return jsonify({"document": doc}), 200


@documents_bp.route("/documents/<document_id>", methods=["DELETE"])
@jwt_required()
def delete_document(document_id: str):
    user_id = get_jwt_identity()
    service = get_document_service()
    service.delete_document(document_id=document_id, user_id=user_id)
    return jsonify({"message": "Document deleted successfully."}), 200
