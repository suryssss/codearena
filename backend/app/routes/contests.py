"""Contest routes — CRUD for admins, list/join for users."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.services.contest_service import ContestService
from app.utils.decorators import admin_required
from app.utils.validators import ContestCreateSchema, ContestUpdateSchema
from app.utils.jwt_helpers import get_current_user_id, get_current_user_claims

contests_bp = Blueprint("contests", __name__)


@contests_bp.route("", methods=["POST"])
@admin_required
def create_contest():
    """Create a new contest (admin only)."""
    data = ContestCreateSchema().load(request.get_json())
    user_id = get_current_user_id()
    contest = ContestService.create_contest(data, admin_id=user_id)
    return jsonify({
        "message": "Contest created",
        "contest": contest.to_dict(),
    }), 201


@contests_bp.route("", methods=["GET"])
def list_contests():
    """List all published contests. Admins see all."""
    is_admin = False
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt
        verify_jwt_in_request()
        claims = get_jwt()
        is_admin = claims.get("is_admin", False)
    except Exception:
        pass

    contests = ContestService.list_contests(published_only=not is_admin)

    # Service may return ORM objects or cached dicts
    if contests and isinstance(contests[0], dict):
        contest_list = contests
    else:
        contest_list = [c.to_dict() for c in contests]

    return jsonify({"contests": contest_list}), 200


@contests_bp.route("/<int:contest_id>", methods=["GET"])
def get_contest(contest_id):
    """Get a single contest with its problems."""
    contest = ContestService.get_contest(contest_id)
    return jsonify({
        "contest": contest.to_dict(include_problems=True),
    }), 200


@contests_bp.route("/<int:contest_id>", methods=["PUT"])
@admin_required
def update_contest(contest_id):
    """Update a contest (admin only)."""
    data = ContestUpdateSchema().load(request.get_json())
    contest = ContestService.update_contest(contest_id, data)
    return jsonify({
        "message": "Contest updated",
        "contest": contest.to_dict(),
    }), 200


@contests_bp.route("/<int:contest_id>", methods=["DELETE"])
@admin_required
def delete_contest(contest_id):
    """Delete a contest (admin only)."""
    ContestService.delete_contest(contest_id)
    return jsonify({"message": "Contest deleted"}), 200


@contests_bp.route("/<int:contest_id>/join", methods=["POST"])
@jwt_required()
def join_contest(contest_id):
    """Join a contest as a participant."""
    user_id = get_current_user_id()
    participant = ContestService.join_contest(contest_id, user_id=user_id)
    return jsonify({
        "message": "Joined contest successfully",
        "participant": participant.to_dict(),
    }), 201


@contests_bp.route("/<int:contest_id>/status", methods=["GET"])
@jwt_required()
def contest_status(contest_id):
    """Check if current user has joined and get contest status."""
    user_id = get_current_user_id()
    contest = ContestService.get_contest(contest_id)
    is_joined = ContestService.is_participant(contest_id, user_id)
    return jsonify({
        "contest_id": contest_id,
        "status": contest.status,
        "is_joined": is_joined,
    }), 200
