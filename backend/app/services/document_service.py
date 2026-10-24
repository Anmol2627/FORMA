import uuid
from pathlib import Path
from typing import List, Dict, Any
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF

from backend.app.repositories.document_repo import DocumentRepository
from backend.app.utils.errors import (
    BadRequestError,
    NotFoundError,
    ForbiddenError,
    AppError
)


class DocumentExtractionService:
    """Reusable service interface for PDF text extraction that future RAG pipelines can also consume directly."""
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> List[Dict[str, Any]]:
        try:
            doc = fitz.open(file_path)
        except Exception as e:
            raise BadRequestError(
                f"The provided file is not a valid or readable PDF: {str(e)}",
                code="invalid_pdf_format"
            ) from e

        pages = []
        try:
            for page_index in range(len(doc)):
                page = doc[page_index]
                text = page.get_text("text").strip()
                pages.append({
                    "page_number": page_index + 1,
                    "char_count": len(text),
                    "text": text
                })
        finally:
            doc.close()

        return pages


class DocumentService:
    def __init__(
        self,
        upload_folder: str,
        max_content_length: int = 10 * 1024 * 1024,
        document_repo: DocumentRepository = None,
        extractor: DocumentExtractionService = None
    ):
        self.upload_folder = Path(upload_folder)
        self.max_content_length = max_content_length
        self.document_repo = document_repo or DocumentRepository()
        self.extractor = extractor or DocumentExtractionService()
        self.upload_folder.mkdir(parents=True, exist_ok=True)

    def upload_and_process_pdf(self, user_id: str, file: FileStorage) -> dict:
        if not file or not file.filename:
            raise BadRequestError("No file uploaded or filename is empty.", code="missing_file")

        original_filename = secure_filename(file.filename)
        if not original_filename.lower().endswith(".pdf"):
            raise BadRequestError(
                "Only PDF files are supported. Please upload a file with a .pdf extension.",
                code="unsupported_file_type"
            )

        # Generate private storage identifier outside any static folder
        private_filename = f"doc_{uuid.uuid4().hex}.pdf"
        target_path = self.upload_folder / private_filename

        try:
            file.save(str(target_path))
            file_size = target_path.stat().st_size

            if file_size == 0:
                raise BadRequestError("Uploaded PDF file is empty.", code="empty_file")

            if file_size > self.max_content_length:
                raise BadRequestError(
                    f"File size exceeds the maximum allowed limit of {self.max_content_length // (1024 * 1024)}MB.",
                    code="file_too_large"
                )

            # Extract text preserving page boundaries
            extracted_pages = self.extractor.extract_text_from_pdf(str(target_path))
            page_count = len(extracted_pages)

            doc = self.document_repo.create(
                owner_id=user_id,
                original_filename=original_filename,
                storage_path=str(target_path),
                file_size_bytes=file_size,
                page_count=page_count,
                extracted_text_metadata=extracted_pages,
                processing_status="ready"
            )

            return doc.to_dict(include_extracted_text=False)

        except Exception as e:
            # Clean up private file on processing failure
            if target_path.exists():
                try:
                    target_path.unlink()
                except OSError:
                    pass
            if isinstance(e, AppError):
                raise e
            raise BadRequestError(f"Failed to process PDF: {str(e)}", code="pdf_processing_error") from e

    def list_documents(self, user_id: str) -> List[dict]:
        documents = self.document_repo.list_by_owner(owner_id=user_id)
        # Never expose raw server file paths or full extracted text in listing
        return [doc.to_dict(include_extracted_text=False) for doc in documents]

    def get_document(self, document_id: str, user_id: str) -> dict:
        doc = self.document_repo.get_by_id(document_id)
        if not doc:
            raise NotFoundError(f"Document '{document_id}' was not found.", code="document_not_found")

        if doc.owner_id != user_id:
            raise ForbiddenError("You are not authorized to access this document.", code="forbidden_document_access")

        return doc.to_dict(include_extracted_text=True)

    def delete_document(self, document_id: str, user_id: str) -> None:
        doc = self.document_repo.get_by_id(document_id)
        if not doc:
            raise NotFoundError(f"Document '{document_id}' was not found.", code="document_not_found")

        if doc.owner_id != user_id:
            raise ForbiddenError("You are not authorized to delete this document.", code="forbidden_document_deletion")

        file_path = Path(doc.storage_path)
        self.document_repo.delete(doc)

        if file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                pass
