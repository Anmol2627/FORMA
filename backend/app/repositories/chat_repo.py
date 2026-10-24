from typing import List, Optional
from backend.app.extensions import db
from backend.app.models.chat import ChatSession, ChatMessage


class ChatRepository:
    @staticmethod
    def get_session_by_id(session_id: str) -> Optional[ChatSession]:
        return db.session.get(ChatSession, session_id)

    @staticmethod
    def list_sessions_for_user(user_id: str) -> List[ChatSession]:
        return (
            ChatSession.query.filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .all()
        )

    @staticmethod
    def create_session(user_id: str, document_id: str, title: str) -> ChatSession:
        session = ChatSession(
            user_id=user_id,
            document_id=document_id,
            title=title.strip()
        )
        db.session.add(session)
        db.session.commit()
        return session

    @staticmethod
    def add_message(
        session_id: str,
        role: str,
        content: str,
        citations: Optional[list] = None
    ) -> ChatMessage:
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content.strip(),
            citations=citations or []
        )
        db.session.add(msg)
        db.session.commit()
        return msg

    @staticmethod
    def get_messages_for_session(session_id: str) -> List[ChatMessage]:
        return (
            ChatMessage.query.filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
