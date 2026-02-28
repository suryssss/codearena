"""Leaderboard routes."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.services.leaderboard_service import LeaderboardService
from app.utils.jwt_helpers import get_current_user_id

leaderboard_bp = Blueprint("leaderboard", __name__)


@leaderboard_bp.route("/<int:contest_id>", methods=["GET"])
def get_leaderboard(contest_id):
    """Get the leaderboard for a contest."""
    rankings = LeaderboardService.get_leaderboard(contest_id)
    return jsonify({
        "contest_id": contest_id,
        "leaderboard": rankings,
    }), 200


@leaderboard_bp.route("/<int:contest_id>/percentile", methods=["GET"])
@jwt_required()
def get_percentile(contest_id):
    """Get the current user's performance percentile."""
    user_id = get_current_user_id()
    percentile = LeaderboardService.get_performance_percentile(contest_id, user_id)
    return jsonify({
        "contest_id": contest_id,
        "user_id": user_id,
        "percentile": percentile,
    }), 200
