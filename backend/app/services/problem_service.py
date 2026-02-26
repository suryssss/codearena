"""Problem service — business logic for problem management."""

from app.extensions import db
from app.models.problem import Problem
from app.models.test_case import TestCase
from app.models.contest import Contest
from app.errors import NotFoundError


class ProblemService:

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
        return problem

    @staticmethod
    def delete_problem(problem_id: int) -> None:
        """Delete a problem and its test cases."""
        problem = Problem.query.get(problem_id)
        if not problem:
            raise NotFoundError("Problem not found")
        db.session.delete(problem)
        db.session.commit()

    @staticmethod
    def get_problem(problem_id: int) -> Problem:
        """Get a single problem."""
        problem = Problem.query.get(problem_id)
        if not problem:
            raise NotFoundError("Problem not found")
        return problem

    @staticmethod
    def list_problems_for_contest(contest_id: int) -> list[Problem]:
        """Get all problems for a specific contest."""
        contest = Contest.query.get(contest_id)
        if not contest:
            raise NotFoundError("Contest not found")
        return Problem.query.filter_by(contest_id=contest_id).all()

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
        return tc

    @staticmethod
    def delete_test_case(test_case_id: int) -> None:
        """Delete a test case."""
        tc = TestCase.query.get(test_case_id)
        if not tc:
            raise NotFoundError("Test case not found")
        db.session.delete(tc)
        db.session.commit()
