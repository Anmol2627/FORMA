import uuid
from datetime import datetime, timezone
from backend.app.extensions import db


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=False, default=0)
    processing_status = db.Column(db.String(50), nullable=False, default="ready")  # "processing", "ready", "failed"
    page_count = db.Column(db.Integer, nullable=False, default=0)
    extracted_text_metadata = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    owner = db.relationship("User", back_populates="documents")
    chat_sessions = db.relationship("ChatSession", back_populates="document", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self, include_extracted_text: bool = False) -> dict:
        """Serializes document without exposing server storage path or full raw text in listings."""
        data = {
            "id": self.id,
            "owner_id": self.owner_id,
            "original_filename": self.original_filename,
            "file_size_bytes": self.file_size_bytes,
            "processing_status": self.processing_status,
            "page_count": self.page_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_extracted_text:
            data["extracted_text_metadata"] = self.extracted_text_metadata
        return data
