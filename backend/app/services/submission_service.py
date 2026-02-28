"""Submission service — handles RUN (sample only) and SUBMIT (full judge) flows."""

from datetime import datetime, timezone

from app.extensions import db
from app.models.submission import Submission
from app.models.problem import Problem
from app.models.contest import Contest
from app.models.test_case import TestCase
from app.models.participant import ContestParticipant
from app.errors import NotFoundError, ForbiddenError, APIError


class SubmissionService:

    # ── RUN Mode ─────────────────────────────────────────────────────
    # Execute only sample test cases
    # Return detailed output (stdout, stderr, stack trace, execution time)
    # Do NOT save to DB, do NOT update leaderboard

    @staticmethod
    def run_code(
        user_id: int,
        problem_id: int,
        contest_id: int,
        code: str,
        language: str = "python",
    ) -> dict:
        """
        Run code against sample test cases only (RUN mode).
        Returns raw output without saving to DB.
        """
        problem = Problem.query.get(problem_id)
        if not problem:
            raise NotFoundError("Problem not found")
        if problem.contest_id != contest_id:
            raise APIError("Problem does not belong to this contest", status_code=400)

        # Get only sample test cases
        sample_cases = TestCase.query.filter_by(
            problem_id=problem_id, is_sample=True,
        ).order_by(TestCase.order).all()

        if not sample_cases:
            # Fallback: use sample_input/sample_output from problem
            if problem.sample_input and problem.sample_output:
                sample_cases_data = [{
                    "input_data": problem.sample_input,
                    "expected_output": problem.sample_output,
                }]
            else:
                return {
                    "status": "no_test_cases",
                    "message": "No sample test cases available",
                    "results": [],
                }
        else:
            sample_cases_data = [
                {"input_data": tc.input_data, "expected_output": tc.expected_output}
                for tc in sample_cases
            ]

        # Run code directly (sync) — no queue needed for RUN mode
        from worker.executor import CodeExecutor
        executor = CodeExecutor(use_docker=False)

        results = []
        overall_status = "passed"

        for i, tc_data in enumerate(sample_cases_data):
            exec_result = executor.execute(
                code=code,
                input_data=tc_data["input_data"],
                timeout=problem.time_limit,
            )

            actual = exec_result["stdout"].strip()
            expected = tc_data["expected_output"].strip()

            # Determine test case verdict
            if exec_result["timed_out"]:
                tc_status = "time_limit_exceeded"
                overall_status = "time_limit_exceeded"
            elif exec_result["exit_code"] != 0:
                tc_status = "runtime_error"
                overall_status = "runtime_error"
            elif actual == expected:
                tc_status = "passed"
            else:
                tc_status = "wrong_answer"
                overall_status = "wrong_answer"

            results.append({
                "test_case": i + 1,
                "status": tc_status,
                "input": tc_data["input_data"],
                "expected_output": expected,
                "actual_output": actual,
                "stdout": exec_result["stdout"],
                "stderr": exec_result["stderr"],  # Detailed errors allowed in RUN mode
                "execution_time": round(exec_result["execution_time"], 4),
            })

            # Stop at first failure (like SUBMIT mode)
            if tc_status != "passed":
                break

        return {
            "status": overall_status,
            "passed": sum(1 for r in results if r["status"] == "passed"),
            "total": len(sample_cases_data),
            "results": results,
        }

    # ── SUBMIT Mode ──────────────────────────────────────────────────
    # Execute ALL hidden test cases
    # Save submission to DB
    # Update leaderboard
    # Return only verdict (no detailed stack traces)

    @staticmethod
    def create_submission(
        user_id: int,
        problem_id: int,
        contest_id: int,
        code: str,
        language: str = "python",
    ) -> Submission:
        """
        Create a new submission and queue it for judging (SUBMIT mode).

        Validates:
        - Problem exists and belongs to the given contest
        - Contest is active
        - User has joined the contest
        """
        # Validate problem
        problem = Problem.query.get(problem_id)
        if not problem:
            raise NotFoundError("Problem not found")
        if problem.contest_id != contest_id:
            raise APIError("Problem does not belong to this contest", status_code=400)

        # Validate contest is active
        contest = Contest.query.get(contest_id)
        if not contest:
            raise NotFoundError("Contest not found")
        if contest.status != "active":
            raise APIError(
                f"Contest is {contest.status}. Submissions are only accepted during active contests.",
                status_code=400,
            )

        # Validate user is a participant
        participant = ContestParticipant.query.filter_by(
            user_id=user_id, contest_id=contest_id,
        ).first()
        if not participant:
            raise ForbiddenError("You must join the contest before submitting")

        # Create submission
        submission = Submission(
            user_id=user_id,
            problem_id=problem_id,
            contest_id=contest_id,
            code=code,
            language=language,
            status=Submission.STATUS_PENDING,
            total_test_cases=problem.test_cases.count(),
        )
        db.session.add(submission)
        db.session.commit()

        # Queue for judging
        SubmissionService._enqueue_judge(submission.id)

        return submission

    @staticmethod
    def _enqueue_judge(submission_id: int) -> None:
        """Push submission to Redis queue, or fall back to sync judging."""
        import app.extensions as ext
        try:
            if ext.redis_client:
                ext.redis_client.rpush("judge_queue", str(submission_id))
                return
        except Exception:
            pass

        # Fallback: run judge synchronously in a background thread
        import threading
        from flask import current_app

        app = current_app._get_current_object()

        def run_judge():
            with app.app_context():
                try:
                    from worker.executor import CodeExecutor
                    from worker.judge import judge_submission
                    executor = CodeExecutor(use_docker=False)
                    judge_submission(submission_id, executor)
                except Exception as e:
                    print(f"[Sync Judge] Error: {e}")

        thread = threading.Thread(target=run_judge, daemon=True)
        thread.start()

    @staticmethod
    def replay_submission(submission_id: int) -> dict:
        """Re-run a submission inside Docker (admin only)."""
        submission = Submission.query.get(submission_id)
        if not submission:
            raise NotFoundError("Submission not found")

        from worker.executor import CodeExecutor
        from worker.judge import judge_submission

        # Reset submission status
        submission.status = Submission.STATUS_PENDING
        submission.test_cases_passed = 0
        submission.execution_time = None
        submission.error_message = None
        db.session.commit()

        # Run judge synchronously
        executor = CodeExecutor(use_docker=False)
        judge_submission(submission_id, executor)

        # Reload
        db.session.refresh(submission)
        return {
            "message": "Submission replayed",
            "submission": submission.to_dict(),
        }

    @staticmethod
    def get_submission(submission_id: int) -> Submission:
        """Get a single submission."""
        submission = Submission.query.get(submission_id)
        if not submission:
            raise NotFoundError("Submission not found")
        return submission

    @staticmethod
    def get_user_submissions(user_id: int, contest_id: int = None) -> list[Submission]:
        """Get all submissions by a user, optionally filtered by contest."""
        query = Submission.query.filter_by(user_id=user_id)
        if contest_id:
            query = query.filter_by(contest_id=contest_id)
        return query.order_by(Submission.created_at.desc()).all()

    @staticmethod
    def get_problem_submissions(problem_id: int, user_id: int = None) -> list[Submission]:
        """Get submissions for a problem, optionally filtered by user."""
        query = Submission.query.filter_by(problem_id=problem_id)
        if user_id:
            query = query.filter_by(user_id=user_id)
        return query.order_by(Submission.created_at.desc()).all()
