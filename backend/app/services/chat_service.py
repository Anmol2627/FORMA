from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from backend.app.models.document import Document
from backend.app.repositories.chat_repo import ChatRepository
from backend.app.repositories.document_repo import DocumentRepository
from backend.app.utils.errors import (
    NotFoundError,
    ForbiddenError,
    NotImplementedCustomError
)


class BaseRAGService(ABC):
    """
    RAG Pipeline Integration Interface.
    Reserved for user implementation (chunking, vector DB, retrieval, and grounded generation).
    """
    @abstractmethod
    def generate_grounded_response(
        self,
        session_id: str,
        document: Document,
        user_query: str,
        chat_history: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Takes the user query and document context and returns:
        (assistant_response_text, citations_list)
        Citations must follow format:
        [{"page_number": int, "snippet": str, "metadata": Optional[dict]}]
        """
        pass


class UnimplementedRAGService(BaseRAGService):
    def generate_grounded_response(
        self,
        session_id: str,
        document: Document,
        user_query: str,
        chat_history: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        raise NotImplementedCustomError(
            message=(
                "The RAG retrieval and answer generation pipeline is currently awaiting implementation. "
                "The chat session and message infrastructure are ready. "
                "Please implement BaseRAGService as documented in docs/RAG_INTEGRATION.md."
            ),
            code="rag_pipeline_not_implemented"
        )


class ChatService:
    def __init__(
        self,
        chat_repo: ChatRepository = None,
        document_repo: DocumentRepository = None,
        rag_service: BaseRAGService = None
    ):
        self.chat_repo = chat_repo or ChatRepository()
        self.document_repo = document_repo or DocumentRepository()
        self.rag_service = rag_service or UnimplementedRAGService()

    def create_session(self, user_id: str, document_id: str, title: Optional[str] = None) -> dict:
        doc = self.document_repo.get_by_id(document_id)
        if not doc:
            raise NotFoundError(f"Document '{document_id}' was not found.", code="document_not_found")

        if doc.owner_id != user_id:
            raise ForbiddenError("You cannot create a chat session for a document you do not own.", code="forbidden_document_access")

        session_title = title.strip() if title else f"Study session: {doc.original_filename}"
        session = self.chat_repo.create_session(
            user_id=user_id,
            document_id=document_id,
            title=session_title
        )
        return session.to_dict()

    def list_sessions(self, user_id: str) -> List[dict]:
        sessions = self.chat_repo.list_sessions_for_user(user_id=user_id)
        return [s.to_dict(include_messages=False) for s in sessions]

    def get_session_messages(self, session_id: str, user_id: str) -> List[dict]:
        session = self.chat_repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundError(f"Chat session '{session_id}' was not found.", code="session_not_found")

        if session.user_id != user_id:
            raise ForbiddenError("You are not authorized to access this chat session.", code="forbidden_session_access")

        messages = self.chat_repo.get_messages_for_session(session_id)
        return [m.to_dict() for m in messages]

    def send_message(self, session_id: str, user_id: str, content: str) -> dict:
        session = self.chat_repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundError(f"Chat session '{session_id}' was not found.", code="session_not_found")

        if session.user_id != user_id:
            raise ForbiddenError("You are not authorized to post messages to this session.", code="forbidden_session_access")

        # Persist the incoming user message
        user_message = self.chat_repo.add_message(
            session_id=session_id,
            role="user",
            content=content.strip()
        )

        # Retrieve prior history for RAG context
        history = [m.to_dict() for m in self.chat_repo.get_messages_for_session(session_id)]

        # Delegate to RAG pipeline (raises 501 NotImplemented until implemented)
        reply_content, citations = self.rag_service.generate_grounded_response(
            session_id=session_id,
            document=session.document,
            user_query=content,
            chat_history=history
        )

        assistant_message = self.chat_repo.add_message(
            session_id=session_id,
            role="assistant",
            content=reply_content,
            citations=citations
        )

        return {
            "user_message": user_message.to_dict(),
            "assistant_message": assistant_message.to_dict(),
        }
