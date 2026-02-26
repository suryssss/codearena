"""Submission routes — submit code, check results."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.services.submission_service import SubmissionService
from app.utils.validators import SubmissionCreateSchema
from app.utils.jwt_helpers import get_current_user_id, get_current_user_claims

submissions_bp = Blueprint("submissions", __name__)


@submissions_bp.route("", methods=["POST"])
@jwt_required()
def create_submission():
    """Submit code for judging."""
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
