"""Proctoring routes — log violations, admin review."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.services.proctoring_service import ProctoringService
from app.utils.decorators import admin_required
from app.utils.jwt_helpers import get_current_user_id

proctoring_bp = Blueprint("proctoring", __name__)

# Violation threshold before flagging a user
VIOLATION_THRESHOLD = 5


@proctoring_bp.route("/violation", methods=["POST"])
@jwt_required()
def log_violation():
    """Log a proctoring violation from the frontend."""
    user_id = get_current_user_id()
    data = request.get_json()

    contest_id = data.get("contest_id")
    violation_type = data.get("violation_type")
    details = data.get("details", "")

    if not contest_id or not violation_type:
        return jsonify({"error": "contest_id and violation_type are required"}), 400

    valid_types = ["tab_switch", "window_blur", "copy_paste", "right_click", "fullscreen_exit"]
    if violation_type not in valid_types:
        return jsonify({"error": f"Invalid violation_type. Must be one of: {valid_types}"}), 400

    violation = ProctoringService.log_violation(
        user_id=user_id,
        contest_id=contest_id,
        violation_type=violation_type,
        details=details,
        threshold=VIOLATION_THRESHOLD,
    )

    return jsonify({
        "message": "Violation logged",
        "violation": violation.to_dict(),
        "total_violations": ProctoringService.get_violation_count(user_id, contest_id),
    }), 201


@proctoring_bp.route("/violations/<int:contest_id>", methods=["GET"])
@admin_required
def get_contest_violations(contest_id):
    """Get all proctoring violations for a contest (admin only)."""
    violations_by_user = ProctoringService.get_contest_violations(contest_id)
    return jsonify({
        "contest_id": contest_id,
        "violations": violations_by_user,
    }), 200


@proctoring_bp.route("/flagged/<int:contest_id>", methods=["GET"])
@admin_required
def get_flagged_users(contest_id):
    """Get all flagged users for a contest (admin only)."""
    flagged = ProctoringService.get_flagged_users(contest_id)
    return jsonify({
        "contest_id": contest_id,
        "flagged_users": flagged,
    }), 200


@proctoring_bp.route("/status/<int:contest_id>", methods=["GET"])
@jwt_required()
def get_my_violations(contest_id):
    """Get current user's violation count for a contest."""
    user_id = get_current_user_id()
    count = ProctoringService.get_violation_count(user_id, contest_id)
    is_flagged = ProctoringService.is_user_flagged(user_id, contest_id)
    return jsonify({
        "contest_id": contest_id,
        "violation_count": count,
        "is_flagged": is_flagged,
        "threshold": VIOLATION_THRESHOLD,
    }), 200
