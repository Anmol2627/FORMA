import uuid
from datetime import datetime, timezone
from backend.app.extensions import db


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = db.Column(db.String(36), db.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = db.relationship("User", back_populates="chat_sessions")
    document = db.relationship("Document", back_populates="chat_sessions")
    messages = db.relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
        lazy="joined"
    )

    def to_dict(self, include_messages: bool = False) -> dict:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "document_title": self.document.original_filename if self.document else None,
            "title": self.title,
            "message_count": len(self.messages) if self.messages else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_messages:
            data["messages"] = [m.to_dict() for m in self.messages]
        return data


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(
        db.String(36),
        db.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role = db.Column(db.String(20), nullable=False)  # "user", "assistant", "system"
    content = db.Column(db.Text, nullable=False)
    citations = db.Column(db.JSON, nullable=True)  # List of citations: [{"page_number": int, "snippet": str}]
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationship
    session = db.relationship("ChatSession", back_populates="messages")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "citations": self.citations or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
