from functools import wraps
from flask import request
from pydantic import BaseModel, ValidationError as PydanticValidationError
from typing import Type, TypeVar
from backend.app.utils.errors import BadRequestError, RequestValidationError

T = TypeVar("T", bound=BaseModel)


def validate_payload(schema_cls: Type[T], data: dict = None) -> T:
    if data is None:
        if not request.is_json:
            raise BadRequestError("Request payload must be JSON", code="invalid_content_type")
        data = request.get_json(silent=True)
        if data is None:
            raise BadRequestError("Invalid or empty JSON body", code="invalid_json")

    try:
        return schema_cls.model_validate(data)
    except PydanticValidationError as e:
        errors_list = []
        for err in e.errors():
            loc = ".".join(str(item) for item in err.get("loc", []))
            errors_list.append({
                "field": loc,
                "message": err.get("msg")
            })
        raise RequestValidationError(message="Validation failed", details=errors_list)


def validate_json(schema_cls: Type[T]):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            validated = validate_payload(schema_cls)
            return fn(*args, validated_data=validated, **kwargs)
        return wrapper
    return decorator
