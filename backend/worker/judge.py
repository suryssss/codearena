"""
Judge worker — pulls submissions from Redis queue and evaluates them.

This runs as a separate process from the Flask app.
Usage: python -m worker.judge
"""

import sys
import os
import time

# Add project root to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.submission import Submission
from app.models.test_case import TestCase
from app.services.leaderboard_service import LeaderboardService
from worker.executor import CodeExecutor
import app.extensions as ext


def judge_submission(submission_id: int, executor: CodeExecutor) -> None:
    """
    Judge a single submission against all test cases.

    Flow:
    1. Load submission and its test cases
    2. Mark as 'running'
    3. Execute code against each test case
    4. Compare output
    5. Update status and score
    6. Emit real-time events via SocketIO
    """
    submission = Submission.query.get(submission_id)
    if not submission:
        print(f"[Judge] Submission {submission_id} not found, skipping")
        return

    # Mark as running
    submission.status = Submission.STATUS_RUNNING
    db.session.commit()

    # Emit running status via SocketIO
    _emit_submission_status(submission)

    # Get test cases
    test_cases = TestCase.query.filter_by(
        problem_id=submission.problem_id,
    ).order_by(TestCase.order).all()

    if not test_cases:
        submission.status = Submission.STATUS_ACCEPTED
        submission.test_cases_passed = 0
        submission.total_test_cases = 0
        db.session.commit()
        _emit_submission_status(submission)
        print(f"[Judge] Submission {submission_id}: No test cases, marking accepted")
        return

    submission.total_test_cases = len(test_cases)
    passed = 0
    max_time = 0.0
    final_status = Submission.STATUS_ACCEPTED

    from app.models.problem import Problem
    problem = Problem.query.get(submission.problem_id)
    time_limit = problem.time_limit if problem else 5.0

    for i, tc in enumerate(test_cases):
        print(f"[Judge] Submission {submission_id}: Running test case {i + 1}/{len(test_cases)}")

        result = executor.execute(
            code=submission.code,
            input_data=tc.input_data,
            timeout=time_limit,
        )

        max_time = max(max_time, result["execution_time"])

        # Check for TLE
        if result["timed_out"]:
            final_status = Submission.STATUS_TIME_LIMIT
            #error message in SUBMIT mode
            submission.error_message = "Time limit exceeded"
            break

        # Check for runtime error
        if result["exit_code"] != 0:
            final_status = Submission.STATUS_RUNTIME_ERROR
            #stack trace in SUBMIT mode
            submission.error_message = "Runtime error"
            break

        # Compare output
        actual = result["stdout"].strip()
        expected = tc.expected_output.strip()

        if actual == expected:
            passed += 1
        else:
            final_status = Submission.STATUS_WRONG_ANSWER
            submission.error_message = f"Wrong answer on test case {i + 1}"
            break

    # Update submission
    submission.status = final_status
    submission.test_cases_passed = passed
    submission.execution_time = round(max_time, 4)
    db.session.commit()

    print(f"[Judge] Submission {submission_id}: {final_status} ({passed}/{len(test_cases)} passed, {max_time:.3f}s)")

    # Emit final result via SocketIO
    _emit_submission_status(submission)

    # Update leaderboard if accepted
    if final_status == Submission.STATUS_ACCEPTED:
        LeaderboardService.recalculate_user_score(
            contest_id=submission.contest_id,
            user_id=submission.user_id,
        )


def _emit_submission_status(submission: Submission) -> None:
    """Emit submission status update via SocketIO."""
    try:
        from app.sockets.events import emit_submission_result
        emit_submission_result(
            contest_id=submission.contest_id,
            submission_data={
                "id": submission.id,
                "user_id": submission.user_id,
                "problem_id": submission.problem_id,
                "contest_id": submission.contest_id,
                "status": submission.status,
                "test_cases_passed": submission.test_cases_passed,
                "total_test_cases": submission.total_test_cases,
                "execution_time": submission.execution_time,
                # No error_message or code in SUBMIT mode events
            },
        )
    except Exception as e:
        print(f"[Judge] SocketIO emit error (non-fatal): {e}")


def run_worker():
    """
    Main worker loop — polls Redis queue for new submissions.
    """
    app = create_app()
    executor = CodeExecutor(use_docker=True)

    print("[Judge Worker] Starting...")
    print(f"[Judge Worker] Docker mode: {executor.use_docker}")
    print("[Judge Worker] Waiting for submissions...")

    with app.app_context():
        redis_client = ext.redis_client

        while True:
            try:
                # BLPOP blocks until a submission is available (5s timeout)
                item = redis_client.blpop("judge_queue", timeout=5)

                if item is None:
                    continue  # Timeout, loop back

                _, submission_id_str = item
                submission_id = int(submission_id_str)
                print(f"\n[Judge Worker] Processing submission {submission_id}")

                judge_submission(submission_id, executor)

            except KeyboardInterrupt:
                print("\n[Judge Worker] Shutting down...")
                break
            except Exception as e:
                print(f"[Judge Worker] Error: {e}")
                time.sleep(1)  # Avoid tight loop on repeated errors


if __name__ == "__main__":
    run_worker()
