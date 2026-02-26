"""Helpers for extracting user info from JWT tokens."""

from flask_jwt_extended import get_jwt_identity, get_jwt


def get_current_user_id() -> int:
    """Get the current user's ID from the JWT identity (stored as string)."""
    return int(get_jwt_identity())


def get_current_user_claims() -> dict:
    """
    Get current user's full claims dict.
    Returns: {"user_id": int, "username": str, "is_admin": bool}
    """
    jwt_data = get_jwt()
    return {
        "user_id": int(get_jwt_identity()),
        "username": jwt_data.get("username", ""),
        "is_admin": jwt_data.get("is_admin", False),
    }
