"""Authentication service — handles registration, login, and token generation."""

import bcrypt
from flask_jwt_extended import create_access_token
from datetime import timedelta

from app.extensions import db
from app.models.user import User
from app.errors import ConflictError, UnauthorizedError


class AuthService:

    @staticmethod
    def register(username: str, email: str, password: str) -> User:
        """Register a new user. Raises ConflictError if user already exists."""
        if User.query.filter_by(email=email).first():
            raise ConflictError("Email already registered")
        if User.query.filter_by(username=username).first():
            raise ConflictError("Username already taken")

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def login(email: str, password: str) -> dict:
        """Authenticate user and return JWT token."""
        user = User.query.filter_by(email=email).first()
        if not user:
            raise UnauthorizedError("Invalid email or password")

        if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
            raise UnauthorizedError("Invalid email or password")

        # Identity MUST be a string for Flask-JWT-Extended v4.x
        additional_claims = {
            "username": user.username,
            "is_admin": user.is_admin,
        }
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=24),
        )

        return {
            "access_token": access_token,
            "user": user.to_dict(),
        }
