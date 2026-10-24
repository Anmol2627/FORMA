from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class AIOptionSchema(BaseModel):
    option_text: str = Field(..., min_length=1)
    is_correct: bool = Field(default=False)
    option_explanation: Optional[str] = Field(default=None, description="Why this option is correct or incorrect")


class AIQuestionSchema(BaseModel):
    prompt: str = Field(..., min_length=1)
    explanation: Optional[str] = Field(default=None)
    difficulty: Optional[str] = Field(default="medium")
    options: List[AIOptionSchema] = Field(..., min_length=2, max_length=6)

    @model_validator(mode="after")
    def validate_single_correct(self):
        correct_count = sum(1 for opt in self.options if opt.is_correct)
        if correct_count != 1:
            raise ValueError(
                f"Generated question must contain exactly one correct option. Found {correct_count}."
            )
        return self


class AIGeneratedQuizPayload(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = Field(default=None)
    questions: List[AIQuestionSchema] = Field(..., min_length=1)


class QuizGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200)
    question_count: int = Field(default=5, ge=1, le=20)
    difficulty: Literal["easy", "medium", "hard"] = Field(default="medium")
    source_text: Optional[str] = Field(default=None, max_length=15000)

    @field_validator("topic")
    @classmethod
    def clean_topic(cls, v: str) -> str:
        t = v.strip()
        if not t:
            raise ValueError("Topic cannot be empty or whitespace only")
        return t
