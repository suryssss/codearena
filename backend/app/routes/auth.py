"""Authentication routes — register, login, profile."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.services.auth_service import AuthService
from app.utils.validators import RegisterSchema, LoginSchema
from app.utils.jwt_helpers import get_current_user_id

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    data = RegisterSchema().load(request.get_json())
    user = AuthService.register(
        username=data["username"],
        email=data["email"],
        password=data["password"],
    )
    return jsonify({
        "message": "User registered successfully",
        "user": user.to_dict(),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login and receive a JWT token."""
    data = LoginSchema().load(request.get_json())
    result = AuthService.login(
        email=data["email"],
        password=data["password"],
    )
    return jsonify(result), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_profile():
    """Get the current user's profile."""
    user_id = get_current_user_id()
    from app.models.user import User
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200
