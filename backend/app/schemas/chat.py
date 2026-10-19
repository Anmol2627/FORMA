from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ChatSessionCreateRequest(BaseModel):
    document_id: str = Field(..., min_length=1)
    title: Optional[str] = Field(default=None, max_length=200)

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            t = v.strip()
            return t or None
        return None


class ChatMessageSendRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)

    @field_validator("content")
    @classmethod
    def clean_content(cls, v: str) -> str:
        t = v.strip()
        if not t:
            raise ValueError("Message content cannot be blank")
        return t
