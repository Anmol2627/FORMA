from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class AnswerSubmitItem(BaseModel):
    question_id: str = Field(..., min_length=1)
    selected_option_id: Optional[str] = Field(default=None)


class AttemptSubmitSchema(BaseModel):
    answers: List[AnswerSubmitItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_duplicate_question_answers(self):
        seen_question_ids = set()
        for item in self.answers:
            if item.question_id in seen_question_ids:
                raise ValueError(
                    f"Duplicate answer submitted for question_id '{item.question_id}'. Each question can only be answered once."
                )
            seen_question_ids.add(item.question_id)
        return self
