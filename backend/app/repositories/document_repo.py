from typing import List, Optional
from backend.app.extensions import db
from backend.app.models.document import Document


class DocumentRepository:
    @staticmethod
    def get_by_id(document_id: str) -> Optional[Document]:
        return db.session.get(Document, document_id)

    @staticmethod
    def list_by_owner(owner_id: str) -> List[Document]:
        return (
            Document.query.filter(Document.owner_id == owner_id)
            .order_by(Document.created_at.desc())
            .all()
        )

    @staticmethod
    def create(
        owner_id: str,
        original_filename: str,
        storage_path: str,
        file_size_bytes: int,
        page_count: int,
        extracted_text_metadata: list,
        processing_status: str = "ready"
    ) -> Document:
        doc = Document(
            owner_id=owner_id,
            original_filename=original_filename,
            storage_path=storage_path,
            file_size_bytes=file_size_bytes,
            page_count=page_count,
            extracted_text_metadata=extracted_text_metadata,
            processing_status=processing_status
        )
        db.session.add(doc)
        db.session.commit()
        return doc

    @staticmethod
    def delete(document: Document) -> None:
        db.session.delete(document)
        db.session.commit()
