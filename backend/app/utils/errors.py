from flask import jsonify
from werkzeug.exceptions import HTTPException
from pydantic import ValidationError as PydanticValidationError


class AppError(Exception):
    def __init__(self, message: str, code: str = "bad_request", status_code: int = 400, details=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details

    def to_dict(self):
        err = {"code": self.code, "message": self.message}
        if self.details is not None:
            err["details"] = self.details
        return {"error": err}


class BadRequestError(AppError):
    def __init__(self, message: str = "Invalid request", code: str = "bad_request", details=None):
        super().__init__(message, code=code, status_code=400, details=details)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required", code: str = "unauthorized"):
        super().__init__(message, code=code, status_code=401)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Access forbidden", code: str = "forbidden"):
        super().__init__(message, code=code, status_code=403)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", code: str = "not_found"):
        super().__init__(message, code=code, status_code=404)


class ConflictError(AppError):
    def __init__(self, message: str = "Resource already exists", code: str = "conflict"):
        super().__init__(message, code=code, status_code=409)


class RequestValidationError(AppError):
    def __init__(self, message: str = "Validation failed", details=None):
        super().__init__(message, code="validation_error", status_code=422, details=details)


class NotImplementedCustomError(AppError):
    def __init__(self, message: str = "Feature not implemented", code: str = "not_implemented"):
        super().__init__(message, code=code, status_code=501)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(PydanticValidationError)
    def handle_pydantic_validation(error: PydanticValidationError):
        errors_list = []
        for err in error.errors():
            loc = ".".join(str(item) for item in err.get("loc", []))
            errors_list.append({
                "field": loc,
                "message": err.get("msg")
            })
        return jsonify({
            "error": {
                "code": "validation_error",
                "message": "Input validation failed",
                "details": errors_list
            }
        }), 422

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        code_map = {
            400: "bad_request",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            405: "method_not_allowed",
            413: "payload_too_large",
            415: "unsupported_media_type",
            422: "unprocessable_entity",
            500: "internal_server_error",
            501: "not_implemented",
        }
        code = code_map.get(error.code, "http_error")
        message = error.description or str(error)
        return jsonify({
            "error": {
                "code": code,
                "message": message
            }
        }), error.code

    @app.errorhandler(Exception)
    def handle_unhandled_exception(error: Exception):
        app.logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        return jsonify({
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred. Please try again later."
            }
        }), 500
