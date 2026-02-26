"""Problem service — business logic for problem management with Redis caching."""

from app.extensions import db
from app.models.problem import Problem
from app.models.test_case import TestCase
from app.models.contest import Contest
from app.errors import NotFoundError
from app.utils.cache import (
    cache_get, cache_set, cache_delete, cache_delete_pattern,
    cache_invalidate_contest,
    TTL_MEDIUM, TTL_LONG,
)


class ProblemService:

    @staticmethod
    def _invalidate_problem_cache(problem_id: int, contest_id: int = None) -> None:
        """Invalidate all caches related to a problem."""
        cache_delete(f"cache:problem:{problem_id}")
        if contest_id:
            cache_delete(f"cache:problems:contest:{contest_id}")

    @staticmethod
    def create_problem(data: dict) -> Problem:
        """Create a problem with optional test cases."""
        contest = Contest.query.get(data["contest_id"])
        if not contest:
            raise NotFoundError("Contest not found")

        problem = Problem(
            contest_id=data["contest_id"],
            title=data["title"],
            description=data["description"],
            input_format=data.get("input_format", ""),
            output_format=data.get("output_format", ""),
            constraints=data.get("constraints", ""),
            sample_input=data.get("sample_input", ""),
            sample_output=data.get("sample_output", ""),
            time_limit=data.get("time_limit", 2.0),
            memory_limit=data.get("memory_limit", 256),
            points=data.get("points", 100),
        )
        db.session.add(problem)
        db.session.flush()  # Get problem.id

        # Add test cases
        for tc_data in data.get("test_cases", []):
            tc = TestCase(
                problem_id=problem.id,
                input_data=tc_data["input_data"],
                expected_output=tc_data["expected_output"],
                is_sample=tc_data.get("is_sample", False),
                order=tc_data.get("order", 0),
            )
            db.session.add(tc)

        db.session.commit()

        # Invalidate problem list cache for this contest
        cache_delete(f"cache:problems:contest:{data['contest_id']}")
        cache_invalidate_contest(data["contest_id"])

        return problem

    @staticmethod
    def update_problem(problem_id: int, data: dict) -> Problem:
        """Update a problem's metadata."""
        problem = Problem.query.get(problem_id)
        if not problem:
            raise NotFoundError("Problem not found")

        for key, value in data.items():
            if hasattr(problem, key) and key != "test_cases":
                setattr(problem, key, value)
        db.session.commit()

        ProblemService._invalidate_problem_cache(problem_id, problem.contest_id)
        return problem

    @staticmethod
    def delete_problem(problem_id: int) -> None:
        """Delete a problem and its test cases."""
        problem = Problem.query.get(problem_id)
        if not problem:
            raise NotFoundError("Problem not found")
        contest_id = problem.contest_id
        db.session.delete(problem)
        db.session.commit()

        ProblemService._invalidate_problem_cache(problem_id, contest_id)

    @staticmethod
    def get_problem(problem_id: int) -> Problem:
        """Get a single problem (cached)."""
        # We return ORM object for route flexibility — cache at route level
        problem = Problem.query.get(problem_id)
        if not problem:
            raise NotFoundError("Problem not found")
        return problem

    @staticmethod
    def list_problems_for_contest(contest_id: int) -> list:
        """Get all problems for a specific contest (cached)."""
        cache_key = f"cache:problems:contest:{contest_id}"
        cached_data = cache_get(cache_key)
        if cached_data is not None:
            return cached_data

        contest = Contest.query.get(contest_id)
        if not contest:
            raise NotFoundError("Contest not found")

        problems = Problem.query.filter_by(contest_id=contest_id).all()

        # Cache serialized problem dicts
        problem_dicts = [p.to_dict() for p in problems]
        cache_set(cache_key, problem_dicts, TTL_MEDIUM)

        return problems

    @staticmethod
    def add_test_case(problem_id: int, data: dict) -> TestCase:
        """Add a test case to a problem."""
        problem = Problem.query.get(problem_id)
        if not problem:
            raise NotFoundError("Problem not found")

        tc = TestCase(
            problem_id=problem_id,
            input_data=data["input_data"],
            expected_output=data["expected_output"],
            is_sample=data.get("is_sample", False),
            order=data.get("order", 0),
        )
        db.session.add(tc)
        db.session.commit()

        ProblemService._invalidate_problem_cache(problem_id, problem.contest_id)
        return tc

    @staticmethod
    def delete_test_case(test_case_id: int) -> None:
        """Delete a test case."""
        tc = TestCase.query.get(test_case_id)
        if not tc:
            raise NotFoundError("Test case not found")
        problem_id = tc.problem_id
        problem = Problem.query.get(problem_id)
        db.session.delete(tc)
        db.session.commit()

        if problem:
            ProblemService._invalidate_problem_cache(problem_id, problem.contest_id)
