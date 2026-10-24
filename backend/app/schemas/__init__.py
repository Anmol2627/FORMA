from backend.app.schemas.auth import RegisterRequest, LoginRequest
from backend.app.schemas.quiz import QuizCreateSchema, QuizUpdateSchema, QuestionCreateSchema, OptionCreateSchema
from backend.app.schemas.attempt import AttemptSubmitSchema, AnswerSubmitItem
from backend.app.schemas.ai import QuizGenerateRequest, AIGeneratedQuizPayload
from backend.app.schemas.chat import ChatSessionCreateRequest, ChatMessageSendRequest

__all__ = [
    "RegisterRequest",
    "LoginRequest",
    "QuizCreateSchema",
    "QuizUpdateSchema",
    "QuestionCreateSchema",
    "OptionCreateSchema",
    "AttemptSubmitSchema",
    "AnswerSubmitItem",
    "QuizGenerateRequest",
    "AIGeneratedQuizPayload",
    "ChatSessionCreateRequest",
    "ChatMessageSendRequest",
]
