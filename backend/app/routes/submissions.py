"""Submission routes — run code, submit code, check results."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.services.submission_service import SubmissionService
from app.utils.validators import SubmissionCreateSchema, RunCodeSchema
from app.utils.jwt_helpers import get_current_user_id, get_current_user_claims

submissions_bp = Blueprint("submissions", __name__)


# ── RUN Mode ─────────────────────────────────────────────────────
# Execute only sample/visible test cases
# Return detailed output (stdout, stderr, stack trace, execution time)
# Do NOT save to DB, do NOT update leaderboard

@submissions_bp.route("/run", methods=["POST"])
@jwt_required()
def run_code():
    """Run code against sample test cases only. Returns detailed output."""
    data = RunCodeSchema().load(request.get_json())
    user_id = get_current_user_id()

    result = SubmissionService.run_code(
        user_id=user_id,
        problem_id=data["problem_id"],
        contest_id=data["contest_id"],
        code=data["code"],
        language=data.get("language", "python"),
    )

    return jsonify(result), 200


# ── SUBMIT Mode ──────────────────────────────────────────────────
# Execute ALL hidden test cases
# Save submission to DB
# Update leaderboard
# Return only verdict (no detailed stack traces)

@submissions_bp.route("", methods=["POST"])
@jwt_required()
def create_submission():
    """Submit code for full judging against all test cases."""
    data = SubmissionCreateSchema().load(request.get_json())
    user_id = get_current_user_id()

    submission = SubmissionService.create_submission(
        user_id=user_id,
        problem_id=data["problem_id"],
        contest_id=data["contest_id"],
        code=data["code"],
        language=data.get("language", "python"),
    )

    return jsonify({
        "message": "Submission received",
        "submission": submission.to_dict(),
    }), 201


@submissions_bp.route("/<int:submission_id>", methods=["GET"])
@jwt_required()
def get_submission(submission_id):
    """Get a single submission's details and result."""
    submission = SubmissionService.get_submission(submission_id)
    result = submission.to_dict()

    # Include code only for the submitting user or admins
    claims = get_current_user_claims()
    if claims["user_id"] == submission.user_id or claims.get("is_admin"):
        result["code"] = submission.code

    return jsonify({"submission": result}), 200


@submissions_bp.route("/my", methods=["GET"])
@jwt_required()
def my_submissions():
    """Get the current user's submissions, optionally filtered by contest."""
    user_id = get_current_user_id()
    contest_id = request.args.get("contest_id", type=int)

    submissions = SubmissionService.get_user_submissions(
        user_id=user_id,
        contest_id=contest_id,
    )
    return jsonify({
        "submissions": [s.to_dict() for s in submissions],
    }), 200


@submissions_bp.route("/problem/<int:problem_id>", methods=["GET"])
@jwt_required()
def problem_submissions(problem_id):
    """Get current user's submissions for a specific problem."""
    user_id = get_current_user_id()
    submissions = SubmissionService.get_problem_submissions(
        problem_id=problem_id,
        user_id=user_id,
    )
    return jsonify({
        "submissions": [s.to_dict() for s in submissions],
    }), 200


# ── Admin: Submission Replay ─────────────────────────────────────

@submissions_bp.route("/<int:submission_id>/replay", methods=["POST"])
@jwt_required()
def replay_submission(submission_id):
    """Re-run a submission inside Docker (admin only)."""
    claims = get_current_user_claims()
    if not claims.get("is_admin"):
        return jsonify({"error": "Admin access required"}), 403

    result = SubmissionService.replay_submission(submission_id)
    return jsonify(result), 200
