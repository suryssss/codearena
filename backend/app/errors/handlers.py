"""
Error handlers for the CodeArena API.
"""

from flask import jsonify
from marshmallow import ValidationError


class APIError(Exception):
    """Base API error class."""

    def __init__(self, message: str, status_code: int = 400, payload: dict = None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self) -> dict:
        result = {"error": self.message}
        if self.payload:
            result["details"] = self.payload
        return result


class NotFoundError(APIError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class UnauthorizedError(APIError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ForbiddenError(APIError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)


class ConflictError(APIError):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, status_code=409)


def register_error_handlers(app):
    """Register global error handlers on the Flask app."""

    @app.errorhandler(APIError)
    def handle_api_error(error):
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return jsonify({"error": "Validation failed", "details": error.messages}), 400

    @app.errorhandler(404)
    def handle_404(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def handle_500(error):
        return jsonify({"error": "Internal server error"}), 500
