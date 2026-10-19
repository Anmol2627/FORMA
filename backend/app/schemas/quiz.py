from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class OptionCreateSchema(BaseModel):
    option_text: str = Field(..., min_length=1, max_length=1000)
    is_correct: bool = Field(default=False)

    @field_validator("option_text")
    @classmethod
    def clean_text(cls, v: str) -> str:
        text = v.strip()
        if not text:
            raise ValueError("Option text cannot be empty or whitespace only")
        return text


class QuestionCreateSchema(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=5000)
    explanation: Optional[str] = Field(default=None, max_length=5000)
    display_position: int = Field(default=0, ge=0)
    topic: Optional[str] = Field(default=None, max_length=100)
    difficulty: Optional[Literal["easy", "medium", "hard"]] = Field(default="medium")
    options: List[OptionCreateSchema] = Field(..., min_length=2, max_length=10)

    @field_validator("prompt")
    @classmethod
    def clean_prompt(cls, v: str) -> str:
        text = v.strip()
        if not text:
            raise ValueError("Question prompt cannot be empty or whitespace only")
        return text

    @model_validator(mode="after")
    def validate_one_correct_option(self):
        correct_count = sum(1 for opt in self.options if opt.is_correct)
        if correct_count != 1:
            raise ValueError(
                f"Each question must have exactly one correct option. Found {correct_count} correct options."
            )
        return self


class QuizCreateSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    visibility: Literal["private", "public"] = Field(default="private")
    generation_metadata: Optional[dict] = Field(default=None)
    questions: List[QuestionCreateSchema] = Field(..., min_length=1, max_length=100)

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        text = v.strip()
        if not text:
            raise ValueError("Quiz title cannot be empty or whitespace only")
        return text


class QuizUpdateSchema(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    visibility: Optional[Literal["private", "public"]] = Field(default=None)
    questions: Optional[List[QuestionCreateSchema]] = Field(default=None, min_length=1, max_length=100)

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            text = v.strip()
            if not text:
                raise ValueError("Quiz title cannot be empty or whitespace only")
            return text
        return v
