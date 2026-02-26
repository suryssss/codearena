"""Submission service — handles code submission and queuing for judge."""

from datetime import datetime, timezone

from app.extensions import db
from app.models.submission import Submission
from app.models.problem import Problem
from app.models.contest import Contest
from app.models.participant import ContestParticipant
from app.errors import NotFoundError, ForbiddenError, APIError


class SubmissionService:

    @staticmethod
    def create_submission(
        user_id: int,
        problem_id: int,
        contest_id: int,
        code: str,
        language: str = "python",
    ) -> Submission:
        """
        Create a new submission and queue it for judging.

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
