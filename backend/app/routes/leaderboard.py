"""Leaderboard routes."""

from flask import Blueprint, jsonify

from app.services.leaderboard_service import LeaderboardService

leaderboard_bp = Blueprint("leaderboard", __name__)


@leaderboard_bp.route("/<int:contest_id>", methods=["GET"])
def get_leaderboard(contest_id):
    """Get the leaderboard for a contest."""
    rankings = LeaderboardService.get_leaderboard(contest_id)
    return jsonify({
        "contest_id": contest_id,
        "leaderboard": rankings,
    }), 200
