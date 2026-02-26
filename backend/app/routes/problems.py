"""Problem routes — CRUD for admins, view for participants."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.services.problem_service import ProblemService
from app.utils.decorators import admin_required
from app.utils.validators import ProblemCreateSchema, ProblemUpdateSchema, TestCaseSchema

problems_bp = Blueprint("problems", __name__)


@problems_bp.route("", methods=["POST"])
@admin_required
def create_problem():
    """Create a new problem with test cases (admin only)."""
    data = ProblemCreateSchema().load(request.get_json())
    problem = ProblemService.create_problem(data)
    return jsonify({
        "message": "Problem created",
        "problem": problem.to_dict(include_test_cases=True),
    }), 201


@problems_bp.route("/<int:problem_id>", methods=["GET"])
def get_problem(problem_id):
    """Get a single problem. Hidden test cases are not shown to non-admins."""
    problem = ProblemService.get_problem(problem_id)
    include_tests = False

    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt
        verify_jwt_in_request()
        claims = get_jwt()
        include_tests = claims.get("is_admin", False)
    except Exception:
        pass

    return jsonify({
        "problem": problem.to_dict(include_test_cases=include_tests),
    }), 200


@problems_bp.route("/<int:problem_id>", methods=["PUT"])
@admin_required
def update_problem(problem_id):
    """Update a problem (admin only)."""
    data = ProblemUpdateSchema().load(request.get_json())
    problem = ProblemService.update_problem(problem_id, data)
    return jsonify({
        "message": "Problem updated",
        "problem": problem.to_dict(),
    }), 200


@problems_bp.route("/<int:problem_id>", methods=["DELETE"])
@admin_required
def delete_problem(problem_id):
    """Delete a problem (admin only)."""
    ProblemService.delete_problem(problem_id)
    return jsonify({"message": "Problem deleted"}), 200


@problems_bp.route("/contest/<int:contest_id>", methods=["GET"])
def list_problems(contest_id):
    """List all problems for a contest."""
    problems = ProblemService.list_problems_for_contest(contest_id)

    # Service may return ORM objects or cached dicts
    if problems and isinstance(problems[0], dict):
        problem_list = problems
    else:
        problem_list = [p.to_dict() for p in problems]

    return jsonify({"problems": problem_list}), 200


@problems_bp.route("/<int:problem_id>/test-cases", methods=["POST"])
@admin_required
def add_test_case(problem_id):
    """Add a test case to a problem (admin only)."""
    data = TestCaseSchema().load(request.get_json())
    tc = ProblemService.add_test_case(problem_id, data)
    return jsonify({
        "message": "Test case added",
        "test_case": tc.to_dict(),
    }), 201


@problems_bp.route("/test-cases/<int:test_case_id>", methods=["DELETE"])
@admin_required
def delete_test_case(test_case_id):
    """Delete a test case (admin only)."""
    ProblemService.delete_test_case(test_case_id)
    return jsonify({"message": "Test case deleted"}), 200
