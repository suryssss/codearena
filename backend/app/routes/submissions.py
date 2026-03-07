"""Submission routes — run code, submit code, check results.

Scaling changes:
- RUN mode is now async: code is queued via Redis and results are
  delivered via SocketIO (run_result event) instead of blocking the
  HTTP request. This prevents 500 concurrent "Run" clicks from
  freezing the API.
- Rate limits on /run (10/min) and /submit (5/min) prevent a single
  user from overwhelming the judge queue.
- A /run/<job_id> polling endpoint is provided as a fallback.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.services.submission_service import SubmissionService
from app.utils.validators import SubmissionCreateSchema, RunCodeSchema
from app.utils.jwt_helpers import get_current_user_id, get_current_user_claims
from app.extensions import limiter

submissions_bp = Blueprint("submissions", __name__)


# RUN Mode (now async)
# Queue code for execution against sample test cases.
# Returns a job_id immediately. Results arrive via SocketIO 'run_result'.
# This is the key change that prevents the API from freezing under load.

@submissions_bp.route("/run", methods=["POST"])
@jwt_required()
@limiter.limit("10/minute")
def run_code():
    """Queue code for async execution against sample test cases."""
    data = RunCodeSchema().load(request.get_json())
    user_id = get_current_user_id()

    result = SubmissionService.run_code_async(
        user_id=user_id,
        problem_id=data["problem_id"],
        contest_id=data["contest_id"],
        code=data["code"],
        language=data.get("language", "python"),
    )

    return jsonify(result), 202  # 202 Accepted — job queued


@submissions_bp.route("/run/<job_id>", methods=["GET"])
@jwt_required()
def get_run_result(job_id):
    """Poll for a RUN mode result (fallback if SocketIO misses it)."""
    result = SubmissionService.get_run_result(job_id)
    if result is None:
        return jsonify({"status": "pending", "job_id": job_id}), 200
    return jsonify(result), 200


# SUBMIT Mode
# Execute ALL hidden test cases
# Save submission to DB
# Update leaderboard
# Return only verdict (no detailed stack traces)

@submissions_bp.route("", methods=["POST"])
@jwt_required()
@limiter.limit("5/minute")
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


# Admin: Submission Replay
@submissions_bp.route("/<int:submission_id>/replay", methods=["POST"])
@jwt_required()
def replay_submission(submission_id):
    """Re-run a submission inside Docker (admin only)."""
    claims = get_current_user_claims()
    if not claims.get("is_admin"):
        return jsonify({"error": "Admin access required"}), 403

    result = SubmissionService.replay_submission(submission_id)
    return jsonify(result), 200
