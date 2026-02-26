"""Custom decorators for route protection."""

from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from app.errors import ForbiddenError


def admin_required(fn):
    """
    Decorator that ensures the current user is an admin.
    Must be used on routes that already require JWT.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if not claims.get("is_admin", False):
            raise ForbiddenError("Admin access required")
        return fn(*args, **kwargs)
    return wrapper
