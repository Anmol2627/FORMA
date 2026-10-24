from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    display_name: str = Field(..., min_length=1, max_length=100)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("display_name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        name = v.strip()
        if not name:
            raise ValueError("Display name cannot be empty or blank")
        return name


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()
